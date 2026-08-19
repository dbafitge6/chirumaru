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
    print("=" * 100)
    print("要確認2件のレコード詳細情報取得")
    print("=" * 100)

    records = fetch_airtable_records()
    print(f"\n取得完了: {len(records)} 件")

    # Find target records
    target_records = {}
    for record in records:
        fields = record.get('fields', {})
        name = fields.get('Store Name', '').lower()

        if 'gelateria nina' in name:
            target_records['gelateria nina'] = record
        elif 'sugar snow' in name:
            target_records['sugar snow'] = record

    # Print details
    print("\n" + "=" * 100)
    print("詳細情報")
    print("=" * 100)

    for store_name in ['gelateria nina', 'sugar snow']:
        record = target_records.get(store_name)

        if record:
            fields = record.get('fields', {})
            print(f"\n【{store_name}】")
            print(f"  Record ID: {record.get('id')}")
            print(f"  店名: {fields.get('Store Name', 'N/A')}")
            print(f"  一言メモ: '{fields.get('一言メモ', 'N/A')}'")
            print(f"  説明: {fields.get('説明', 'N/A')}")
            print(f"  メニュー: {fields.get('メニュー', 'N/A')}")
            print(f"  営業時間: {fields.get('営業時間', 'N/A')}")
            print(f"  住所: {fields.get('住所', 'N/A')}")
            print(f"  営業形態: {fields.get('営業形態', 'N/A')}")
            print(f"  シーンタグ: {fields.get('シーンタグ', [])}")
            print(f"  タグ: {fields.get('タグ', [])}")
        else:
            print(f"\n【{store_name}】")
            print("  Not found in database")

if __name__ == '__main__':
    main()
