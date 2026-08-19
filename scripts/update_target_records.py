#!/usr/bin/env python3
"""
要修正・要確認レコードの Airtable 反映スクリプト
1. dessert café marutoshikaku → 一言メモ更新
2. sugar snow → 一言メモ更新
3. gelateria nina → 2店舗に分割登録
"""

import os
import sys
import requests
from pathlib import Path

# Configuration
AIRTABLE_BASE_ID = "appyyoKM7RprQRht8"
AIRTABLE_TABLE_ID = "tblcOdcqCxzb7kX0e"
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN')

def fetch_airtable_records():
    """Fetch all records from Airtable"""
    if not AIRTABLE_TOKEN:
        print("Error: AIRTABLE_TOKEN not set")
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
            print(f"Error: {response.status_code}")
            print(response.text)
            sys.exit(1)

        data = response.json()
        all_records.extend(data.get('records', []))

        offset = data.get('offset')
        if not offset:
            break

    return all_records

def update_record(record_id, new_tagline):
    """Update a single record's 一言メモ"""
    headers = {'Authorization': f'Bearer {AIRTABLE_TOKEN}'}
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}/{record_id}'

    payload = {
        'fields': {
            '一言メモ': new_tagline
        }
    }

    response = requests.patch(url, json=payload, headers=headers)
    return response.status_code == 200

def create_record(fields):
    """Create a new record"""
    headers = {'Authorization': f'Bearer {AIRTABLE_TOKEN}'}
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}'

    payload = {'records': [{'fields': fields}]}

    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 201, response.json()

def main():
    print("=" * 100)
    print("Airtable レコード更新スクリプト")
    print("=" * 100)

    # Fetch all records
    print("\n📥 Airtable からデータを取得中...")
    records = fetch_airtable_records()
    print(f"✅ 取得完了: {len(records)} 件")

    # Find target records
    target_records = {
        'dessert_cafe': None,
        'sugar_snow': None,
        'gelateria_nina': None
    }

    for record in records:
        fields = record.get('fields', {})
        name = fields.get('Store Name', '').lower()

        if 'dessert café marutoshikaku' in name:
            target_records['dessert_cafe'] = record
        elif 'sugar snow' in name:
            target_records['sugar_snow'] = record
        elif 'gelateria nina' in name:
            target_records['gelateria_nina'] = record

    # Prepare updates
    updates = []

    # 1. dessert café marutoshikaku
    if target_records['dessert_cafe']:
        record_id = target_records['dessert_cafe']['id']
        new_tagline = 'ノエルピスタチオツリー/フレーズショコラパルフェ'
        updates.append(('update', 'dessert café marutoshikaku', record_id, new_tagline))

    # 2. sugar snow
    if target_records['sugar_snow']:
        record_id = target_records['sugar_snow']['id']
        # 修正案：海の家の特徴を含む
        new_tagline = '夏季営業の浜カフェ、ジェラートとスイーツ'
        updates.append(('update', 'sugar snow', record_id, new_tagline))

    # 3. gelateria nina - Split into 2 locations
    if target_records['gelateria_nina']:
        old_record = target_records['gelateria_nina']
        record_id = old_record['id']
        fields = old_record.get('fields', {})

        # Get base information
        base_fields = {
            'シーンタグ': fields.get('シーンタグ', []),
            'タグ': fields.get('タグ', []),
            'メニュー': fields.get('メニュー', ''),
            '説明': fields.get('説明', ''),
            '営業時間': fields.get('営業時間', ''),
            '住所': fields.get('住所', '')
        }

        # Itakura store (original - 1号店)
        itakura_fields = base_fields.copy()
        itakura_fields['Store Name'] = 'gelateria nina 板倉店'
        itakura_fields['一言メモ'] = '板倉1号店。14種類のジェラート、季節限定フレーバーあり'
        itakura_fields['住所'] = '〒944-0131 上越市板倉区針752'

        # Honmachi store (new, Takada area - 2号店)
        honmachi_fields = base_fields.copy()
        honmachi_fields['Store Name'] = 'gelateria nina 本町店'
        honmachi_fields['一言メモ'] = '本町2号店。高田駅近く、14種類のジェラート専門店'
        honmachi_fields['住所'] = '〒943-0832 上越市本町1-3-1'

        updates.append(('update', 'gelateria nina 板倉店', record_id, '常時14種のジェラート、季節限定あり', itakura_fields))
        updates.append(('create', 'gelateria nina 本町店', honmachi_fields))

    # Execute updates
    print("\n" + "=" * 100)
    print("更新内容")
    print("=" * 100)

    results = []

    for update in updates:
        if update[0] == 'update':
            if len(update) == 4:
                action, name, record_id, new_tagline = update
                success = update_record(record_id, new_tagline)
                status = "✅" if success else "❌"
                print(f"{status} {name}: '{new_tagline}'")
                results.append((name, success))
            else:
                action, name, record_id, new_tagline, fields = update
                # Update the record name
                success = update_record(record_id, new_tagline)
                status = "✅" if success else "❌"
                print(f"{status} {name}: '{new_tagline}'")
                results.append((name, success))

        elif update[0] == 'create':
            action, name, fields = update
            success, response = create_record(fields)
            status = "✅" if success else "❌"
            print(f"{status} {name}: 新規作成")
            results.append((name, success))

    # Summary
    print("\n" + "=" * 100)
    print("処理結果")
    print("=" * 100)
    success_count = sum(1 for _, success in results if success)
    print(f"成功: {success_count}/{len(results)}")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

if __name__ == '__main__':
    main()
