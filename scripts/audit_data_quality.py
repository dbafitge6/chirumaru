#!/usr/bin/env python3
"""
Airtable データの品質監査
- 重複住所・電話番号の検出
- 説明文の店名と店名フィールドの不一致検出
"""

import os
import requests
import re
from pathlib import Path
from collections import defaultdict

# .env ファイルを読み込む
env_file = Path(__file__).parent.parent / ".env"
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

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 全レコード取得
print("=" * 80)
print("Airtable データ品質監査")
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
        'area': fields.get('fld6sCx8y2OxZV5So', ''),
        'address': fields.get('fldRSjYp5plmTfpYj', ''),  # Address
        'phone': fields.get('fldXUn1lBPuWePGPN', ''),  # Phone
        'description': fields.get('fld7kYvLqO0lLFEWU', ''),
    })

print(f"データ構造化完了: {len(shops)} 店舗\n")

# 【調査1】住所または電話番号の重複
print("=" * 80)
print("【調査1】住所・電話番号の重複検出")
print("=" * 80)

# 住所の重複
address_map = defaultdict(list)
phone_map = defaultdict(list)

for shop in shops:
    if shop['address']:
        address_map[shop['address']].append(shop)
    if shop['phone']:
        phone_map[shop['phone']].append(shop)

# 住所が重複しているもの
duplicate_addresses = {addr: shops_list for addr, shops_list in address_map.items()
                       if len(shops_list) > 1}

# 電話番号が重複しているもの
duplicate_phones = {phone: shops_list for phone, shops_list in phone_map.items()
                    if len(shops_list) > 1}

print(f"\n🔍 住所が重複: {len(duplicate_addresses)} グループ")
if duplicate_addresses:
    for addr, shops_list in sorted(duplicate_addresses.items()):
        print(f"\n📍 {addr}")
        for shop in shops_list:
            print(f"   - ID: {shop['id']}")
            print(f"     店名: {shop['name']}")
            print(f"     エリア: {shop['area']}")

print(f"\n🔍 電話番号が重複: {len(duplicate_phones)} グループ")
if duplicate_phones:
    for phone, shops_list in sorted(duplicate_phones.items()):
        print(f"\n☎️  {phone}")
        for shop in shops_list:
            print(f"   - ID: {shop['id']}")
            print(f"     店名: {shop['name']}")
            print(f"     住所: {shop['address']}")

# 【調査2】説明文の冒頭の店名と店名フィールドの不一致
print("\n" + "=" * 80)
print("【調査2】説明文の店名と店名フィールドの不一致検出")
print("=" * 80)

mismatches = []

for shop in shops:
    if not shop['description']:
        continue

    # 説明文の冒頭から店名を抽出（最初の句点までまたは30文字まで）
    desc_first_part = shop['description'].split('。')[0]
    if len(desc_first_part) > 50:
        desc_first_part = shop['description'][:50]

    # 説明文から店名パターンを抽出
    # パターン1: "〇〇〇は..." または "〇〇〇が..." という形式
    patterns = [
        r'^([^\（()は、。]*)[は、。]',  # 〇〇〇は/〇〇〇、/〇〇〇。
        r'^([^\（()が、。]*)[が、。]',  # 〇〇〇が/〇〇〇、/〇〇〇。
    ]

    extracted_name = None
    for pattern in patterns:
        match = re.search(pattern, shop['description'])
        if match:
            extracted_name = match.group(1).strip()
            break

    if extracted_name and extracted_name not in shop['name'] and shop['name'] not in extracted_name:
        mismatches.append({
            'id': shop['id'],
            'shop_name': shop['name'],
            'desc_name': extracted_name,
            'description': shop['description'][:100]
        })

print(f"\n🔍 不一致: {len(mismatches)} 件\n")

for mismatch in mismatches:
    print(f"⚠️  ID: {mismatch['id']}")
    print(f"   店名フィールド: {mismatch['shop_name']}")
    print(f"   説明文の冒頭: {mismatch['desc_name']}")
    print(f"   説明文: {mismatch['description']}...")
    print()

# 【サマリ】
print("=" * 80)
print("【サマリ】")
print("=" * 80)
print(f"\n総レコード数: {len(shops)}")
print(f"住所重複グループ: {len(duplicate_addresses)}")
print(f"電話番号重複グループ: {len(duplicate_phones)}")
print(f"説明文の店名不一致: {len(mismatches)}")

if duplicate_addresses or duplicate_phones or mismatches:
    print("\n⚠️  問題が検出されました")
else:
    print("\n✅ 検出された問題はありません")

print("\n" + "=" * 80)
