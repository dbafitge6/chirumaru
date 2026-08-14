#!/usr/bin/env python3
"""
「ランチあり」が付いている126件のメニューを Airtable から抽出
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

MENU_FIELD = "fldy7L16dxfRmpPVa"
SCENE_FIELD = "fldDl6OsS4EKmJT18"
STORE_NAME_FIELD = "fldpEdbx8RE5XfBln"

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

print("=" * 80)
print("「ランチあり」が付いているレコードを抽出中...")
print("=" * 80)

all_records = []
offset = None

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

print(f"全レコード取得: {len(all_records)} 件\n")

# 「ランチあり」が付いているレコードを抽出
lunch_records = []
for record in all_records:
    fields = record.get('fields', {})
    tags = fields.get(SCENE_FIELD, [])
    if isinstance(tags, list) and "ランチあり" in tags:
        lunch_records.append({
            'name': fields.get(STORE_NAME_FIELD, 'Unknown'),
            'menu': fields.get(MENU_FIELD, '')
        })

print(f"「ランチあり」が付いているレコード: {len(lunch_records)} 件\n")

# ファイルに保存
os.makedirs("logs", exist_ok=True)
with open("logs/lunch_menus.txt", "w", encoding="utf-8") as f:
    for i, rec in enumerate(lunch_records, 1):
        f.write(f"{i}. {rec['name']}\n")
        f.write(f"   {rec['menu']}\n")
        f.write("\n")

print("=" * 80)
print(f"ログを保存しました: logs/lunch_menus.txt ({len(lunch_records)} 件)")
print("=" * 80)
