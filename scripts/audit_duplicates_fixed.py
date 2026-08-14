#!/usr/bin/env python3
"""
住所・電話番号の重複検出（修正版）
- 住所を正規化（「新潟県」の有無、全角半角、ハイフンの種類を統一）
- 電話番号を正規化（ハイフン・空白を除去）
- 完全一致で検出
"""

import os
import requests
import re
from pathlib import Path
from collections import defaultdict

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

def normalize_address(addr):
    """住所を正規化
    - 「新潟県」を前置する
    - ハイフン・空白を統一
    """
    if not addr:
        return ""

    # 前後の空白を除去
    addr = addr.strip()

    # 「新潟県」が含まれていなければ追加
    if '新潟県' not in addr and '新潟' in addr:
        # 「新潟市」「新潟県」の判定
        if not addr.startswith('新潟県'):
            # 先頭が「新潟市」などの場合
            if addr.startswith('新潟'):
                addr = '新潟県' + addr

    # 全角ハイフン「−」を半角「-」に統一
    addr = addr.replace('−', '-').replace('ー', '-').replace('〜', '-')

    # 空白を除去
    addr = addr.replace(' ', '').replace('　', '')

    return addr

def normalize_phone(phone):
    """電話番号を正規化
    - ハイフン・空白・括弧を除去
    """
    if not phone:
        return ""

    phone = phone.strip()
    # ハイフン・空白・括弧を除去
    phone = re.sub(r'[\s\-（）()−−]', '', phone)

    return phone

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 全レコード取得
print("=" * 80)
print("住所・電話番号の重複検出（修正版）")
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

# データ構造化と正規化
shops = []
for record in all_records:
    fields = record.get('fields', {})
    shops.append({
        'id': record['id'],
        'name': fields.get('fldpEdbx8RE5XfBln', ''),
        'address_raw': fields.get('fld4UiMRxLFmrCIfj', ''),
        'phone_raw': fields.get('fldvO5qOtZYZaCFpm', ''),
        'address_norm': normalize_address(fields.get('fld4UiMRxLFmrCIfj', '')),
        'phone_norm': normalize_phone(fields.get('fldvO5qOtZYZaCFpm', '')),
    })

print("✅ 正規化完了\n")

# 【調査1】住所の重複
print("=" * 80)
print("【調査1】住所の重複検出")
print("=" * 80)

address_map = defaultdict(list)
for shop in shops:
    if shop['address_norm']:
        address_map[shop['address_norm']].append(shop)

duplicate_addresses = {addr: shops_list for addr, shops_list in address_map.items()
                       if len(shops_list) > 1}

print(f"\n🔍 住所が重複: {len(duplicate_addresses)} グループ\n")

if duplicate_addresses:
    for addr_norm, shops_list in sorted(duplicate_addresses.items()):
        print(f"📍 {addr_norm}")
        for shop in shops_list:
            print(f"   - ID: {shop['id']}")
            print(f"     店名: {shop['name']}")
            print(f"     住所（原形）: {shop['address_raw']}")

# 【調査2】電話番号の重複
print("\n" + "=" * 80)
print("【調査2】電話番号の重複検出")
print("=" * 80)

phone_map = defaultdict(list)
for shop in shops:
    if shop['phone_norm']:
        phone_map[shop['phone_norm']].append(shop)

duplicate_phones = {phone: shops_list for phone, shops_list in phone_map.items()
                    if len(shops_list) > 1}

print(f"\n🔍 電話番号が重複: {len(duplicate_phones)} グループ\n")

if duplicate_phones:
    for phone_norm, shops_list in sorted(duplicate_phones.items()):
        print(f"☎️  {phone_norm}")
        for shop in shops_list:
            print(f"   - ID: {shop['id']}")
            print(f"     店名: {shop['name']}")
            print(f"     住所: {shop['address_raw']}")
            print(f"     電話（原形）: {shop['phone_raw']}")

# 【サマリ】
print("\n" + "=" * 80)
print("【サマリ】")
print("=" * 80)
print(f"\n総レコード数: {len(shops)}")
print(f"住所重複グループ: {len(duplicate_addresses)}")
print(f"電話番号重複グループ: {len(duplicate_phones)}")

if duplicate_addresses or duplicate_phones:
    print("\n⚠️  問題が検出されました")
else:
    print("\n✅ 重複は検出されていません")

print("\n" + "=" * 80)
