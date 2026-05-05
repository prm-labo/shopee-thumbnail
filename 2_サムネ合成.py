from PIL import Image
import numpy as np
from pathlib import Path

# ===========================
# 設定（変更禁止）
# ===========================
IMAGE_DIR  = Path('output/images')
OUTPUT_DIR = Path('output/thumbnails')
TEMPLATE   = Path('template.png')

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# テンプレートの商品配置エリア座標
LEFT    = 23
TOP     = 340
RIGHT   = 1026
BOTTOM  = 860
PADDING = 40

# ===========================
# メイン処理
# ===========================
def main():
    # テンプレート確認
    if not TEMPLATE.exists():
        print('エラー: template.png が見つかりません。')
        print('template.png を shopee_thumbnail フォルダに入れてから再実行してください。')
        return

    tmpl = Image.open(TEMPLATE).convert('RGB')

    # テンプレートサイズ確認
    if tmpl.size != (1050, 1050):
        print(f'エラー: template.png のサイズが {tmpl.size} です。')
        print('1050×1050px で作成し直してください。')
        return

    tmpl_arr = np.array(tmpl)

    FW = RIGHT - LEFT - PADDING * 2
    FH = BOTTOM - TOP - PADDING * 2

    imgs = sorted(IMAGE_DIR.glob('*.jpg'))
    total = len(imgs)

    if total == 0:
        print('エラー: output/images/ に画像がありません。')
        print('先に 1_画像取得.py を実行してください。')
        return

    print(f'▶ {total}件のサムネイルを合成します...')
    success = error = 0

    for img_path in imgs:
        out_path = OUTPUT_DIR / img_path.name
        try:
            src = Image.open(img_path).convert('RGB')
            arr = np.array(src)
            h, w = arr.shape[:2]

            # 右上ロゴエリアを除外して商品部分を検出
            arr_clean = arr.copy()
            arr_clean[0:h//4, w*3//4:] = 255

            non_white = ~(
                (arr_clean[:, :, 0] > 240) &
                (arr_clean[:, :, 1] > 240) &
                (arr_clean[:, :, 2] > 240)
            )
            rows = np.where(non_white.any(axis=1))[0]
            cols = np.where(non_white.any(axis=0))[0]

            if len(rows) > 10 and len(cols) > 10:
                product = src.crop((
                    int(cols[0]), int(rows[0]),
                    int(cols[-1]), int(rows[-1])
                ))
            else:
                product = src

            # テンプレートの商品エリアにリサイズして中央配置
            ratio = min(FW / product.width, FH / product.height)
            new_w = int(product.width  * ratio)
            new_h = int(product.height * ratio)
            resized = product.resize((new_w, new_h), Image.LANCZOS)

            result = tmpl.copy()
            paste_x = LEFT + PADDING + (FW - new_w) // 2
            paste_y = TOP  + PADDING + (FH - new_h) // 2
            result.paste(resized, (paste_x, paste_y))

            # テンプレートの上部・下部を復元
            result_arr = np.array(result)
            result_arr[0:200, :]  = tmpl_arr[0:200, :]
            result_arr[860:,  :]  = tmpl_arr[860:,  :]

            Image.fromarray(result_arr).save(out_path, 'JPEG', quality=95)
            success += 1

            if success % 100 == 0:
                print(f'  [{success}/{total}] 処理中...')

        except Exception as e:
            print(f'  {img_path.stem} エラー: {e}')
            error += 1

    print(f'\n完了: 成功={success}件 エラー={error}件')
    print(f'合成済み画像は output/thumbnails/ に保存されました')
    print('\n次のステップ: output/thumbnails/ を開いて合成結果を目視確認してください')

if __name__ == '__main__':
    main()
