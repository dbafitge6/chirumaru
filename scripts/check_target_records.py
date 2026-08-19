#!/usr/bin/env python3
"""
要確認2件のレコード詳細情報を Airtable から取得
"""

import os
import sys
import json
import requests

# Configuration
AIRTABLE_BASE_ID = "appyyoKM7RprQRht8"
AIRTABLE_TABLE_ID = "tblcOdcqCxzb7kX0e"
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN')

def fetch_airtable_records():
    """Fetch all records from Airtable"""
    if not AIRTABLE_TOKEN:
        print("Error: AIRTABLE_TOKEN environment variable not set")
        sys.exit(1)

    headers = {'Authorization': f'Bearer {AIRTABLE_TOKEN}'}
    all_records = []
    offset = None

    while True:
        params = {'pageSize': 100}
        if offset:
            params['offset'] = offset

        response = requests.get(
            f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            print(f"Error: Airtable API returned {response.status_code}")
            print(response.text)
            sys.exit(1)

        data = response.json()
        all_records.extend(data.get('records', []))

        offset = data.get('offset')
        if not offset:
            break

    return all_records

def main():
    output = []
    output.append("=" * 100)
    output.append("要確認2件のレコード詳細情報取得")
    output.append("=" * 100)

    records = fetch_airtable_records()
    output.append(f"\n取得完了: {len(records)} 件")

    # Find target records
    target_records = {}
    for record in records:
        fields = record.get('fields', {})
        name = fields.get('Store Name', '').lower()

        if 'gelateria nina' in name:
            target_records['gelateria nina'] = record
        elif 'sugar snow' in name:
            target_records['sugar snow'] = record

    # Prepare details
    output.append("\n" + "=" * 100)
    output.append("詳細情報")
    output.append("=" * 100)

    for store_name in ['gelateria nina', 'sugar snow']:
        record = target_records.get(store_name)

        if record:
            fields = record.get('fields', {})
            output.append(f"\n【{store_name}】")
            output.append(f"  Record ID: {record.get('id')}")
            output.append(f"  店名: {fields.get('Store Name', 'N/A')}")
            output.append(f"  一言メモ: '{fields.get('一言メモ', 'N/A')}'")
            output.append(f"  説明: {fields.get('説明', 'N/A')}")
            output.append(f"  メニュー: {fields.get('メニュー', 'N/A')}")
            output.append(f"  営業時間: {fields.get('営業時間', 'N/A')}")
            output.append(f"  住所: {fields.get('住所', 'N/A')}")
            output.append(f"  営業形態: {fields.get('営業形態', 'N/A')}")
            output.append(f"  シーンタグ: {fields.get('シーンタグ', [])}")
            output.append(f"  タグ: {fields.get('タグ', [])}")
        else:
            output.append(f"\n【{store_name}】")
            output.append("  Not found in database")

    # Print to stdout
    result_text = "\n".join(output)
    print(result_text)

    # Save to file
    Path("logs").mkdir(exist_ok=True)
    with open("logs/target_records_info.md", 'w', encoding='utf-8') as f:
        f.write(result_text)

if __name__ == '__main__':
    main()
