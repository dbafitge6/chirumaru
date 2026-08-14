#!/usr/bin/env python3
"""
ログから採用した一言をAirtableの「一言」フィールドに書き込む
"""

import os
import re
import requests
import random
from pathlib import Path
from datetime import datetime

env_file = Path(".env")
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

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# ==========================================
# Step 1: ログから採用レコード(店名, 一言)を抽出
# ==========================================
print("【1】ログから採用レコードを抽出中...")

log_path = Path("logs/tagline_gen.md")
adopted_data = {}  # {店名: 一言}

with open(log_path, encoding='utf-8') as f:
    content = f.read()

# テーブル行を抽出（バッチごと）
# | # | 店名 | ... | 生成した一言 | 文字数 | 状態 |
pattern = r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(\w+)\s*\|'

for match in re.finditer(pattern, content):
    shop_name = match.group(1).strip()
    desc_excerpt = match.group(2).strip()
    tagline = match.group(3).strip()
    char_count = match.group(4).strip()
    status = match.group(5).strip()

    if status == "採用" and tagline != "(空)":
        adopted_data[shop_name] = tagline

print(f"✅ 採用レコード {len(adopted_data)} 件を抽出しました\n")

# ==========================================
# Step 2: Airtableから全レコード取得
# ==========================================
print("【2】Airtableから全レコード取得中...")

all_records = []
offset = None

while True:
    params = {"returnFieldsByFieldId": "true"}
    if offset:
        params["offset"] = offset

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ API エラー: {response.status_code}")
        print(response.text)
        exit(1)

    data = response.json()
    all_records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break

print(f"✅ 取得完了: {len(all_records)} 件\n")

# ==========================================
# Step 3: フィールド情報を取得
# ==========================================
print("【3】フィールド情報を確認中...")

# スキーマ取得
schema_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
schema_response = requests.get(schema_url, headers=headers)
schema_data = schema_response.json()

field_map = {}
tagline_field_id = None

for table in schema_data.get('tables', []):
    if table['id'] == TABLE_NAME:
        for field in table.get('fields', []):
            field_map[field['name']] = field['id']
            if field['name'] == '一言':
                tagline_field_id = field['id']
        break

# 「一言」フィールドが存在しなければ作成
if not tagline_field_id:
    print("⚠️  「一言」フィールドが見つかりません。作成します...")

    create_field_url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/fields"
    field_data = {
        "fields": [{
            "name": "一言",
            "type": "singleLineText"
        }]
    }

    response = requests.post(create_field_url, json=field_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ フィールド作成エラー: {response.status_code}")
        print(response.text)
        exit(1)

    response_data = response.json()
    tagline_field_id = response_data['fields'][0]['id']
    print(f"✅ 「一言」フィールドを作成しました: {tagline_field_id}\n")
else:
    print(f"✅ 「一言」フィールドを確認しました: {tagline_field_id}\n")

# ==========================================
# Step 4: 店名でマッピング→更新データ準備
# ==========================================
print("【4】更新データを準備中...")

name_field_id = field_map.get('店名', 'fldpEdbx8RE5XfBln')

# 店名 → record_id のマッピング
shop_to_record = {}
for record in all_records:
    fields = record.get('fields', {})
    shop_name = fields.get(name_field_id, '')
    shop_to_record[shop_name] = record['id']

# 更新するレコード
updates = []
matched_count = 0
unmatched = []

for shop_name, tagline in adopted_data.items():
    if shop_name in shop_to_record:
        record_id = shop_to_record[shop_name]
        updates.append({
            "id": record_id,
            "fields": {
                tagline_field_id: tagline
            }
        })
        matched_count += 1
    else:
        unmatched.append(shop_name)

print(f"✅ マッチ済み: {matched_count} 件")
if unmatched:
    print(f"⚠️  マッチなし: {len(unmatched)} 件")
    for shop in unmatched[:5]:
        print(f"  - {shop}")
    if len(unmatched) > 5:
        print(f"  ... 他 {len(unmatched) - 5} 件")
print()

# ==========================================
# Step 5: Airtableに書き込む
# ==========================================
print("【5】Airtableに書き込み中...")

# バッチサイズ10で更新
batch_size = 10
total_updated = 0

for i in range(0, len(updates), batch_size):
    batch = updates[i:i+batch_size]
    batch_data = {"records": batch}

    response = requests.patch(url, json=batch_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ 書き込みエラー (バッチ {i//batch_size + 1}): {response.status_code}")
        print(response.text)
        exit(1)

    total_updated += len(batch)
    print(f"  バッチ {i//batch_size + 1}: {len(batch)} 件書き込み完了")

print(f"\n✅ 合計 {total_updated} 件をAirtableに書き込みました\n")

# ==========================================
# Step 6: 10件をランダムに取得して検証
# ==========================================
print("【6】検証: ランダムに10件を再取得中...")

# 新しくレコード取得
all_records_latest = []
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
    all_records_latest.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break

# ランダムに10件を選択
sample_records = random.sample(all_records_latest, min(10, len(all_records_latest)))

print(f"\n📋 検証結果（ランダムサンプル 10件）:\n")
print("=" * 80)

verification_results = []
for record in sample_records:
    record_id = record['id']
    fields = record.get('fields', {})
    shop_name = fields.get(name_field_id, 'N/A')
    tagline = fields.get(tagline_field_id, '')

    if shop_name in adopted_data:
        expected = adopted_data[shop_name]
        match = "✅" if tagline == expected else "❌"
        status = "一致" if tagline == expected else "不一致"
    else:
        expected = "(未対象)"
        match = "✓" if not tagline else "？"
        status = "対象外" if not tagline else "予期しない値"

    print(f"{match} {shop_name}")
    print(f"   書き込み: {tagline}")
    if expected != "(未対象)":
        print(f"   期待値:  {expected}")
    print(f"   {status}\n")

    verification_results.append({
        'shop': shop_name,
        'written': tagline,
        'expected': expected,
        'match': match == "✅"
    })

print("=" * 80)

# 最終検証サマリー
matches = sum(1 for r in verification_results if r['match'])
print(f"\n✅ 検証完了: {matches}/10 が期待値と一致\n")

if matches == 10:
    print("🎉 すべてのサンプルが検証に合格しました！")
else:
    print(f"⚠️  {10 - matches}件に不一致があります")

print(f"\n【完了レポート】")
print(f"- 採用レコード: {matched_count} 件をAirtableに書き込み")
print(f"- 空レコード: {len(adopted_data) - matched_count} 件はスキップ")
print(f"- マッチなし: {len(unmatched)} 件（店名が異なる可能性）")
print(f"- 検証: {matches}/10 件一致")
