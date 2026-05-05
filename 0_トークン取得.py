import hmac
import hashlib
import time
import requests
import webbrowser

# ===========================
# ここに入力してください
# ===========================
PARTNER_ID  = input("PARTNER_IDを入力してください: ").strip()
PARTNER_KEY = input("PARTNER_KEYを入力してください: ").strip()
REGION      = input("REGIONを入力してください（ph または sg）: ").strip()

PARTNER_ID = int(PARTNER_ID)

# ===========================
# 認証URLを生成する
# ===========================
def make_auth_url():
    path = '/api/v2/shop/auth_partner'
    ts   = int(time.time())

    if REGION == 'ph':
        redirect = 'https://shopee.ph'
    else:
        redirect = 'https://shopee.sg'

    base_string = f'{PARTNER_ID}{path}{ts}'
    sign = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

    url = (
        f'https://partner.shopeemobile.com{path}'
        f'?partner_id={PARTNER_ID}'
        f'&redirect={redirect}'
        f'&timestamp={ts}'
        f'&sign={sign}'
    )
    return url

# ===========================
# codeからACCESS_TOKENを取得する
# ===========================
def get_access_token(code, shop_id):
    path = '/api/v2/auth/token/get'
    ts   = int(time.time())

    base_string = f'{PARTNER_ID}{path}{ts}'
    sign = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

    url = f'https://partner.shopeemobile.com{path}'
    params = {
        'partner_id': PARTNER_ID,
        'timestamp':  ts,
        'sign':       sign
    }
    payload = {
        'code':       code,
        'shop_id':    int(shop_id),
        'partner_id': PARTNER_ID
    }
    resp = requests.post(url, params=params, json=payload)
    return resp.json()

# ===========================
# メイン処理
# ===========================
def main():
    print('\n' + '='*50)
    print('STEP 1: 認証URLを生成しています...')
    print('='*50)

    auth_url = make_auth_url()

    print('\n以下のURLをブラウザで開いてShopeeにログインしてください。')
    print('（自動でブラウザが開きます）\n')
    print(auth_url)

    # 自動でブラウザを開く
    webbrowser.open(auth_url)

    print('\n' + '='*50)
    print('STEP 2: ログイン後の作業')
    print('='*50)
    print('\nShopeeにログインすると、ブラウザのURLが変わります。')
    print('変わったURLをそのままコピーしてください。')
    print('\n例：https://shopee.ph?code=xxxxxxxx&shop_id=123456789')
    print('      ↑このURLをコピーしてください\n')

    redirected_url = input('ログイン後のURLをここに貼り付けてください: ').strip()

    # URLからcodeとshop_idを取り出す
    try:
        from urllib.parse import urlparse, parse_qs
        parsed  = urlparse(redirected_url)
        params  = parse_qs(parsed.query)
        code    = params['code'][0]
        shop_id = params['shop_id'][0]
    except Exception:
        print('\nエラー: URLの形式が正しくありません。')
        print('ログイン後のURLをそのままコピーして貼り付けてください。')
        return

    print('\n' + '='*50)
    print('STEP 3: ACCESS_TOKENを取得しています...')
    print('='*50)

    data = get_access_token(code, shop_id)

    access_token  = data.get('access_token')
    refresh_token = data.get('refresh_token')

    if not access_token:
        print('\nエラー: ACCESS_TOKENの取得に失敗しました。')
        print('エラー内容:', data)
        print('\nもう一度最初からやり直してください。')
        return

    print('\n' + '='*50)
    print('✅ 取得成功！')
    print('='*50)
    print('\n以下の情報を 設定ファイル.env に貼り付けてください。\n')
    print(f'SHOP_ID={shop_id}')
    print(f'PARTNER_ID={PARTNER_ID}')
    print(f'PARTNER_KEY={PARTNER_KEY}')
    print(f'ACCESS_TOKEN={access_token}')
    print(f'REGION={REGION}')
    print('\n' + '='*50)
    print('⚠️  ACCESS_TOKENには有効期限があります。')
    print('エラーが出た場合はこのスクリプトを再実行してください。')
    print('='*50 + '\n')

if __name__ == '__main__':
    main()
