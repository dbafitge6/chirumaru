#!/usr/bin/env python3
"""
ランチあり タグ誤判定修正スクリプト
判定語「サンド」を削除し、「サンドイッチ」のみに変更
"""

import os
import requests
from pathlib import Path

# .env ファイルを読み込む
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

BASE_ID = "appyyoKM7RprQRht8"
TABLE_NAME = "Stores"
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")

MENU_FIELD = "fldy7L16dxfRmpPVa"  # メニュー
SCENE_FIELD = "fldDl6OsS4EKmJT18"  # シーン
STORE_NAME_FIELD = "fldpEdbx8RE5XfBln"  # 店名

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

def is_lunch_available_fixed(menu_text):
    """修正版：セット・プレート除外、サンドウィッチ表記ゆれ対応"""
    if not menu_text:
        return False

    keywords = ['サンドイッチ', 'サンドウィッチ', 'パスタ', 'カレー', 'ピザ', '定食',
                '丼', 'ランチ', 'モーニング', 'ハンバーグ', 'グラタン', 'ドリア',
                'オムライス', 'ピラフ']

    for kw in keywords:
        if kw in menu_text:
            return True

    return False

print("=" * 80)
print("ランチあり タグ 誤判定修正")
print("=" * 80)

# 全レコード取得
all_records = []
offset = None

print("\n【Step 1】全384件を取得中...")
while True:
    params = {"pageSize": 100, "returnFieldsByFieldId": "true"}
    if offset:
        params["offset"] = offset

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ API エラー: {response.status_code}")
        exit(1)

    data = response.json()
    all_records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break

print(f"取得完了: {len(all_records)} 件\n")

# 現在「ランチあり」が付いているレコードを抽出
print("【Step 2】現在「ランチあり」が付いているレコードを抽出中...")

current_lunch = []
for record in all_records:
    fields = record.get('fields', {})
    tags = fields.get(SCENE_FIELD, [])
    if isinstance(tags, list) and "ランチあり" in tags:
        current_lunch.append({
            'id': record['id'],
            'name': fields.get(STORE_NAME_FIELD, 'Unknown'),
            'menu': fields.get(MENU_FIELD, ''),
            'tags': tags
        })

print(f"現在「ランチあり」が付いているレコード: {len(current_lunch)} 件\n")

# 修正版ロジックで再判定
print("【Step 3】修正版ロジック（「サンドイッチ」のみ）で再判定中...")

lunch_remains = []
lunch_removed = []

for rec in current_lunch:
    lunch_new = is_lunch_available_fixed(rec['menu'])

    if lunch_new:
        lunch_remains.append(rec)
    else:
        lunch_removed.append(rec)

print(f"修正後もランチありが残る: {len(lunch_remains)} 件")
print(f"タグが外れる: {len(lunch_removed)} 件\n")

# ログファイルに保存
log_output = []
log_output.append("=" * 80)
log_output.append("ランチあり タグ 誤判定修正 結果")
log_output.append("=" * 80)
log_output.append("")
log_output.append(f"修正前: {len(current_lunch)} 件（「ランチあり」付与）")
log_output.append(f"修正後: {len(lunch_remains)} 件（「ランチあり」維持）")
log_output.append(f"除外: {len(lunch_removed)} 件")
log_output.append("")
log_output.append("=" * 80)
log_output.append("修正後も「ランチあり」が残るレコード")
log_output.append("=" * 80)
log_output.append("")

for i, rec in enumerate(lunch_remains, 1):
    log_output.append(f"{i}. {rec['name']}")
    log_output.append(f"   メニュー: {rec['menu']}")
    log_output.append("")

log_output.append("")
log_output.append("=" * 80)
log_output.append("タグが外れるレコード（新潟のデザートサンド系）")
log_output.append("=" * 80)
log_output.append("")

for i, rec in enumerate(lunch_removed, 1):
    log_output.append(f"{i}. {rec['name']}")
    log_output.append(f"   メニュー: {rec['menu']}")
    log_output.append("")

# ログを出力
log_text = "\n".join(log_output)
print(log_text)

# ファイルに保存
os.makedirs("logs", exist_ok=True)
with open("logs/lunch_tag_fix.txt", "w", encoding="utf-8") as f:
    f.write(log_text)

print("\n" + "=" * 80)
print("ログを保存しました: logs/lunch_tag_fix.txt")
print("=" * 80)
print("\n⚠️  Airtable への書き込みは実行していません")
print("上記の修正内容をご確認ください。")

