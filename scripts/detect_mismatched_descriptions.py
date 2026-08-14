#!/usr/bin/env python3
"""
説明文に他店舗の店名が含まれているレコードを検出
- 384件全体から店名リストを作成
- 各レコードの説明文に、自分以外の店名が含まれるかチェック
- 2文字以下または一般語のみの店名は除外
"""

import os
import requests
from pathlib import Path
import re

# .env ファイルを読み込む
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_NAME = "Stores"
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")

# 除外する一般語（これだけの店名は除外）
GENERIC_WORDS = {
    'カフェ', '珈琲', 'コーヒー', 'コヒー', 'パン', 'ケーキ', 'パティスリー',
    'パン屋', 'ジェラート', 'アイス', 'スイーツ', '喫茶', '食堂', 'レストラン',
    'バー', 'ワインバー', 'ラウンジ', 'カフェバー', '焙煎', '焙煎所',
}

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 全レコード取得
print("=" * 80)
print("説明文に他店舗の店名が含まれているレコードを検出")
print("=" * 80)
print("\n【Step 1】全レコードを取得中...\n")

all_records = []
offset = None

while True:
    params = {"returnFieldsByFieldId": "true"}
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

print(f"✅ 取得完了: {len(all_records)} 件\n")

# データ構造化
shops = []
for record in all_records:
    fields = record.get('fields', {})
    shops.append({
        'id': record['id'],
        'name': fields.get('fldpEdbx8RE5XfBln', ''),
        'description': fields.get('fld7kYvLqO0lLFEWU', ''),
    })

# 【Step 2】店名リストから検索用リストを作成
print("【Step 2】店名リストから検索用リストを準備中...\n")

# 有効な店名のみを抽出（2文字以上で、一般語でない）
valid_shop_names = []
for shop in shops:
    name = shop['name'].strip()
    # 2文字以下は除外
    if len(name) <= 2:
        continue
    # 一般語のみの店名は除外
    if name in GENERIC_WORDS:
        continue
    valid_shop_names.append((shop['id'], name))

print(f"✅ 有効な店名: {len(valid_shop_names)} 件")
print(f"   （除外: 2文字以下 + 一般語のみ）\n")

# 【Step 3】各レコードの説明文をチェック
print("【Step 3】説明文のスキャン中...\n")

mismatches = []

for shop in shops:
    if not shop['description']:
        continue

    found_other_names = []

    # 自分以外の店名が説明文に含まれるかチェック
    for shop_id, shop_name in valid_shop_names:
        if shop_id == shop['id']:
            # 自分の店名は除外
            continue

        # 説明文に店名が含まれるかチェック
        if shop_name in shop['description']:
            found_other_names.append(shop_name)

    if found_other_names:
        mismatches.append({
            'id': shop['id'],
            'name': shop['name'],
            'found_names': found_other_names,
            'description': shop['description'][:50]
        })

# 【結果表示】
print("=" * 80)
print(f"【検出結果】{len(mismatches)} 件\n")

if mismatches:
    print(f"{'レコードID':<20} {'店名':<30} {'説明文に含まれる他店名':<50} {'説明文冒頭'}")
    print("-" * 150)

    for match in mismatches:
        # 他店名をカンマ区切りで表示
        other_names = ', '.join(match['found_names'])
        print(f"{match['id']:<20} {match['name']:<30} {other_names:<50} {match['description']}")

    print("\n" + "=" * 80)
else:
    print("✅ 説明文に他店舗の店名が含まれているレコードはありません\n")
    print("=" * 80)
