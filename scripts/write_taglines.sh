#!/bin/bash
set -e

# 環境変数を読み込む
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

BASE_ID="appyyoKM7RprQRht8"
TABLE_ID="tblcOdcqCxzb7kX0e"
API_URL="https://api.airtable.com/v0/${BASE_ID}/${TABLE_ID}"

if [ -z "$AIRTABLE_TOKEN" ]; then
    echo "❌ AIRTABLE_TOKEN が設定されていません"
    exit 1
fi

echo "【1】ログから採用レコードを抽出中..."

# ログファイルから採用レコード（店名と一言）をJSONで抽出
adopted_json=$(python3 << 'EOFPYTHON'
import re
import json

log_path = "logs/tagline_gen.md"
adopted_data = {}

with open(log_path, encoding='utf-8') as f:
    content = f.read()

# テーブル行を抽出
pattern = r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(\w+)\s*\|'

for match in re.finditer(pattern, content):
    shop_name = match.group(1).strip()
    tagline = match.group(3).strip()
    status = match.group(5).strip()

    if status == "採用" and tagline != "(空)":
        adopted_data[shop_name] = tagline

print(json.dumps(adopted_data))
EOFPYTHON
)

echo "✅ 採用レコードを抽出しました"
echo

echo "【2】Airtableから全レコード取得中..."

# Airtableから全レコードを取得
records_json=$(curl -s \
  -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  "$API_URL?returnFieldsByFieldId=true" | jq -c '.records | map({id: .id, fields: .fields})')

echo "✅ レコード取得完了"
echo

echo "【3】フィールドスキーマを確認中..."

# メタデータから店名フィールドIDと一言フィールドIDを取得
schema=$(curl -s \
  -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  "https://api.airtable.com/v0/meta/bases/$BASE_ID/tables" | jq ".tables[] | select(.id == \"$TABLE_ID\")")

# 店名フィールドID（既存）
name_field=$(echo "$schema" | jq -r '.fields[] | select(.name == "店名") | .id' | head -1)
echo "  店名フィールド: $name_field"

# 一言フィールドIDを取得、なければ作成
tagline_field=$(echo "$schema" | jq -r '.fields[] | select(.name == "一言") | .id' | head -1)

if [ -z "$tagline_field" ] || [ "$tagline_field" == "null" ]; then
    echo "⚠️  「一言」フィールドが見つかりません。作成します..."

    create_response=$(curl -s -X POST \
      -H "Authorization: Bearer $AIRTABLE_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"fields":[{"name":"一言","type":"singleLineText"}]}' \
      "https://api.airtable.com/v0/$BASE_ID/$TABLE_ID/fields")

    tagline_field=$(echo "$create_response" | jq -r '.fields[0].id')
    echo "✅ 「一言」フィールドを作成しました: $tagline_field"
else
    echo "✅ 「一言」フィールドを確認しました: $tagline_field"
fi
echo

echo "【4】更新データを準備中..."

# 店名→record_id マッピングと更新データの準備
update_data=$(python3 << EOFPYTHON2
import json
import sys

# 入力
adopted_data = json.loads($adopted_json)
records = json.loads('''$records_json''')

name_field = "$name_field"
tagline_field = "$tagline_field"

# 店名→record_id マッピング
shop_to_record = {}
for record in records:
    shop_name = record.get('fields', {}).get(name_field, '')
    if shop_name:
        shop_to_record[shop_name] = record['id']

# 更新するレコード
updates = []
matched = 0

for shop_name, tagline in adopted_data.items():
    if shop_name in shop_to_record:
        updates.append({
            "id": shop_to_record[shop_name],
            "fields": {
                tagline_field: tagline
            }
        })
        matched += 1

print(f"マッチ済み: {matched}", file=sys.stderr)
print(json.dumps(updates))
EOFPYTHON2
)

matched_count=$(echo "$update_data" 2>&1 | grep "マッチ済み" | awk '{print $NF}')
updates=$(echo "$update_data" | tail -1)

echo "✅ $matched_count 件の更新データを準備しました"
echo

echo "【5】Airtableに書き込み中..."

# バッチサイズ10で更新
batch_size=10
total_records=$(echo "$updates" | jq 'length')

for ((i=0; i<$total_records; i+=batch_size)); do
  batch=$(echo "$updates" | jq -c ".[$i:$((i+batch_size))]")

  curl -s -X PATCH \
    -H "Authorization: Bearer $AIRTABLE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"records\": $batch}" \
    "$API_URL" > /dev/null

  batch_num=$((i/batch_size + 1))
  batch_len=$(echo "$batch" | jq 'length')
  echo "  バッチ $batch_num: $batch_len 件書き込み完了"
done

echo "✅ 合計 $total_records 件をAirtableに書き込みました"
echo

echo "【6】検証: ランダムに10件を再取得中..."
echo

# 全レコードを再取得
all_records=$(curl -s \
  -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  "$API_URL?returnFieldsByFieldId=true" | jq '.records')

# ランダムに10件を抽出して検証
python3 << EOFPYTHON3
import json
import random

adopted_data = json.loads($adopted_json)
records = json.loads('''$all_records''')

name_field = "$name_field"
tagline_field = "$tagline_field"

# ランダムに10件を選択
sample = random.sample(records, min(10, len(records)))

print("=" * 80)
print("📋 検証結果（ランダムサンプル 10件）:\n")

match_count = 0

for record in sample:
    fields = record.get('fields', {})
    shop_name = fields.get(name_field, 'N/A')
    tagline = fields.get(tagline_field, '')

    if shop_name in adopted_data:
        expected = adopted_data[shop_name]
        is_match = tagline == expected
        match_mark = "✅" if is_match else "❌"
        status = "一致" if is_match else "不一致"
        if is_match:
            match_count += 1
    else:
        expected = "(未対象)"
        is_match = not tagline
        match_mark = "✓" if is_match else "？"
        status = "対象外" if not tagline else "予期しない値"

    print(f"{match_mark} {shop_name}")
    print(f"   書き込み: {tagline}")
    if expected != "(未対象)":
        print(f"   期待値:  {expected}")
    print(f"   {status}\n")

print("=" * 80)
print(f"\n✅ 検証完了: {match_count}/10 が期待値と一致")

if match_count == 10:
    print("\n🎉 すべてのサンプルが検証に合格しました！")
else:
    print(f"\n⚠️  {10 - match_count}件に不一致があります")

print(f"\n【完了レポート】")
print(f"- 採用レコード: $matched_count 件をAirtableに書き込み")
print(f"- 検証: {match_count}/10 件一致")
EOFPYTHON3
