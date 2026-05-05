import os
import hmac
import hashlib
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# ===========================
# 設定ファイルの読み込み
# ===========================
load_dotenv('設定ファイル.env')

PARTNER_ID   = int(os.getenv('PARTNER_ID'))
PARTNER_KEY  = os.getenv('PARTNER_KEY')
SHOP_ID      = int(os.getenv('SHOP_ID'))
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REGION       = os.getenv('REGION')

BASE_URL = 'https://partner.shopeemobile.com'
IMAGE_DIR = Path('output/images')
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ===========================
# 署名生成
# ===========================
def make_sign(path):
    ts = int(time.time())
    base = f'{PARTNER_ID}{path}{ts}{ACCESS_TOKEN}{SHOP_ID}'
    sign = hmac.new(PARTNER_KEY.encode(), base.encode(), hashlib.sha256).hexdigest()
    return ts, sign

# ===========================
# 商品IDを全件取得
# ===========================
def get_all_item_ids():
    path = '/api/v2/product/get_item_list'
    item_ids = []
    offset = 0
    page_size = 100

    while True:
        ts, sign = make_sign(path)
        params = {
            'partner_id': PARTNER_ID,
            'shop_id': SHOP_ID,
            'access_token': ACCESS_TOKEN,
            'timestamp': ts,
            'sign': sign,
            'offset': offset,
            'page_size': page_size,
            'item_status': 'NORMAL'
        }
        resp = requests.get(BASE_URL + path, params=params)
        data = resp.json()

        items = data.get('response', {}).get('item', [])
        if not items:
            break

        for item in items:
            item_ids.append(item['item_id'])

        if not data.get('response', {}).get('has_next_page', False):
            break

        offset += page_size
        time.sleep(0.5)

    return item_ids

# ===========================
# 商品画像URLを取得
# ===========================
def get_image_urls(item_ids):
    path = '/api/v2/product/get_item_base_info'
    result = {}

    for i in range(0, len(item_ids), 50):
        chunk = item_ids[i:i+50]
        ts, sign = make_sign(path)
        params = {
            'partner_id': PARTNER_ID,
            'shop_id': SHOP_ID,
            'access_token': ACCESS_TOKEN,
            'timestamp': ts,
            'sign': sign,
            'item_id_list': ','.join(map(str, chunk))
        }
        resp = requests.get(BASE_URL + path, params=params)
        data = resp.json()

        for item in data.get('response', {}).get('item_list', []):
            item_id = item['item_id']
            urls = item.get('image', {}).get('image_url_list', [])
            if urls:
                result[item_id] = urls[0]

        time.sleep(0.5)

    return result

# ===========================
# 画像をダウンロード
# ===========================
def download_images(image_map):
    total = len(image_map)
    success = 0

    for item_id, url in image_map.items():
        save_path = IMAGE_DIR / f'{item_id}.jpg'
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                success += 1
                if success % 50 == 0:
                    print(f'  [{success}/{total}] ダウンロード中...')
        except Exception as e:
            print(f'  {item_id} エラー: {e}')

    return success

# ===========================
# メイン処理
# ===========================
def main():
    print('▶ 商品IDを取得中...')
    item_ids = get_all_item_ids()
    print(f'  商品数: {len(item_ids)}件')

    print('▶ 画像URLを取得中...')
    image_map = get_image_urls(item_ids)

    print(f'▶ 画像をダウンロード中...')
    success = download_images(image_map)

    # CSVに商品IDを保存（アップロード時に使用）
    csv_path = Path('output/items.csv')
    with open(csv_path, 'w') as f:
        f.write('item_id\n')
        for item_id in image_map.keys():
            f.write(f'{item_id}\n')

    print(f'\n完了: {success}件の画像を output/images/ に保存しました')

if __name__ == '__main__':
    main()
