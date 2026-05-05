import os
import hmac
import hashlib
import time
import requests
import base64
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

BASE_URL      = 'https://partner.shopeemobile.com'
THUMBNAIL_DIR = Path('output/thumbnails')
ITEMS_CSV     = Path('output/items.csv')

# ===========================
# 署名生成
# ===========================
def make_sign(path):
    ts = int(time.time())
    base = f'{PARTNER_ID}{path}{ts}{ACCESS_TOKEN}{SHOP_ID}'
    sign = hmac.new(PARTNER_KEY.encode(), base.encode(), hashlib.sha256).hexdigest()
    return ts, sign

# ===========================
# 画像をShopeeにアップロード
# ===========================
def upload_image(image_path):
    path = '/api/v2/media_space/upload_image'
    ts, sign = make_sign(path)
    params = {
        'partner_id': PARTNER_ID,
        'shop_id': SHOP_ID,
        'access_token': ACCESS_TOKEN,
        'timestamp': ts,
        'sign': sign
    }
    with open(image_path, 'rb') as f:
        files = {'file': (image_path.name, f, 'image/jpeg')}
        resp = requests.post(BASE_URL + path, params=params, files=files)

    data = resp.json()
    image_id = data.get('response', {}).get('image_id')
    return image_id

# ===========================
# 商品のサムネイルを更新
# ===========================
def update_item_image(item_id, image_id):
    path = '/api/v2/product/update_item'
    ts, sign = make_sign(path)
    params = {
        'partner_id': PARTNER_ID,
        'shop_id': SHOP_ID,
        'access_token': ACCESS_TOKEN,
        'timestamp': ts,
        'sign': sign
    }
    payload = {
        'item_id': item_id,
        'image': {
            'image_id_list': [image_id]
        }
    }
    resp = requests.post(BASE_URL + path, params=params, json=payload)
    data = resp.json()

    error = data.get('error', '')
    if error:
        return False, data.get('message', '不明なエラー')
    return True, None

# ===========================
# メイン処理
# ===========================
def main():
    # 合成済み画像の確認
    if not THUMBNAIL_DIR.exists() or not list(THUMBNAIL_DIR.glob('*.jpg')):
        print('エラー: output/thumbnails/ に画像がありません。')
        print('先に 2_サムネ合成.py を実行してください。')
        return

    # 商品IDリストの読み込み
    if not ITEMS_CSV.exists():
        print('エラー: output/items.csv が見つかりません。')
        print('先に 1_画像取得.py を実行してください。')
        return

    with open(ITEMS_CSV) as f:
        item_ids = [int(line.strip()) for line in f.readlines()[1:] if line.strip()]

    total   = len(item_ids)
    success = skip = error = 0

    print(f'▶ {total}件のサムネイルをアップロードします...')

    for idx, item_id in enumerate(item_ids, 1):
        img_path = THUMBNAIL_DIR / f'{item_id}.jpg'

        if not img_path.exists():
            skip += 1
            continue

        try:
            # 画像をアップロードしてimage_idを取得
            image_id = upload_image(img_path)
            if not image_id:
                print(f'  [{idx}/{total}] {item_id} — 画像アップロード失敗')
                error += 1
                continue

            # 商品のサムネイルを更新
            ok, msg = update_item_image(item_id, image_id)
            if ok:
                success += 1
                if success % 50 == 0:
                    print(f'  [{idx}/{total}] 処理中...')
            else:
                print(f'  [{idx}/{total}] {item_id} — 更新エラー: {msg}')
                error += 1

            time.sleep(0.3)

        except Exception as e:
            print(f'  [{idx}/{total}] {item_id} — 例外エラー: {e}')
            error += 1

    print(f'\n完了: 成功={success}件 スキップ={skip}件 エラー={error}件')
    print('Shopee Seller Center で商品一覧を確認してください')

if __name__ == '__main__':
    main()
