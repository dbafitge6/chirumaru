#!/usr/bin/env python3
"""
既存タグの完全一致判定を検証
修正前後で各名物カテゴリの店舗数を比較
"""

import os
import requests
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

# テスト対象カテゴリ
TEST_CATEGORIES = ["パン", "ケーキ", "クレープ", "プリン", "パンケーキ", "ドーナツ"]
FRANCHISE_CHAINS = ['ドトール', 'タリーズ', 'スターバックス', 'コメダ']

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 全レコード取得
print("=" * 80)
print("既存タグ完全一致判定の検証")
print("=" * 80)
print("\n【Step 1】Airtable から全店舗を取得中...\n")

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

print(f"✅ 取得完了: {len(all_records)} 店舗\n")

# フランチャイズ除外
shops_list = []
for record in all_records:
    fields = record.get('fields', {})
    name = fields.get('fldpEdbx8RE5XfBln', 'Unknown')
    is_franchise = any(chain in name for chain in FRANCHISE_CHAINS)

    if not is_franchise:
        shops_list.append({
            'id': record['id'],
            'name': name,
            'area': fields.get('fld6sCx8y2OxZV5So', 'Unknown'),
            'existing_tags': fields.get('fldsh2ess7aYHhJ8e', '')
        })

print(f"✅ フランチャイズ除外後: {len(shops_list)} 店舗\n")

# 【修正前】部分一致での検索結果
print("=" * 80)
print("【修正前】部分一致で検索した場合")
print("=" * 80)

before_results = defaultdict(list)
for category in TEST_CATEGORIES:
    for shop in shops_list:
        if category in shop['existing_tags']:
            before_results[category].append(shop['name'])

for category in TEST_CATEGORIES:
    count = len(before_results[category])
    print(f"\n📌 {category}: {count} 店舗")
    if count > 0:
        for name in sorted(before_results[category]):
            print(f"   - {name}")

# 【修正後】完全一致での検索結果
print("\n" + "=" * 80)
print("【修正後】完全一致で検索した場合")
print("=" * 80)

after_results = defaultdict(list)
for category in TEST_CATEGORIES:
    for shop in shops_list:
        tags = [t.strip() for t in shop['existing_tags'].split('/')]
        if category in tags:
            after_results[category].append(shop['name'])

for category in TEST_CATEGORIES:
    count = len(after_results[category])
    print(f"\n📌 {category}: {count} 店舗")
    if count > 0:
        for name in sorted(after_results[category]):
            print(f"   - {name}")

# 【修正前後の比較】
print("\n" + "=" * 80)
print("【修正前後の変化】")
print("=" * 80)

for category in TEST_CATEGORIES:
    before_count = len(before_results[category])
    after_count = len(after_results[category])

    if before_count != after_count:
        print(f"\n⚠️  {category}:")
        print(f"   修正前: {before_count} 店舗 → 修正後: {after_count} 店舗 (差分: {after_count - before_count})")

        # 削除された店舗
        removed = set(before_results[category]) - set(after_results[category])
        if removed:
            print(f"   削除されたもの（誤検出）:")
            for name in sorted(removed):
                print(f"     - {name}")
    else:
        print(f"\n✅ {category}: 変化なし ({after_count} 店舗)")

print("\n" + "=" * 80)
