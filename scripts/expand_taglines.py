#!/usr/bin/env python3
"""
一言メモが短い店舗の拡張案を生成するスクリプト
- Airtable から 20字以下の一言メモを持つ店舗を抽出
- Claude API を使って 35字以内の拡張案を生成
- 結果をログファイルに出力
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
import anthropic

# Configuration
AIRTABLE_BASE_ID = "appyyoKM7RprQRht8"
AIRTABLE_TABLE_ID = "tblcOdcqCxzb7kX0e"
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN')
CLAUDE_API_KEY = os.environ.get('CONSULTANT_API_KEY')

TAGLINE_CHAR_LIMIT = 20
EXPANSION_CHAR_LIMIT = 35
MAX_BATCH_SIZE = 50

# Ensure directories exist
Path("logs").mkdir(exist_ok=True)

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

def extract_short_tagline_stores(records):
    """Extract stores with taglines <= 20 characters"""
    short_tagline_stores = []

    for record in records:
        fields = record.get('fields', {})
        tagline = fields.get('一言メモ', '').strip()

        # Check if tagline exists and is <= 20 characters
        if tagline and len(tagline) <= TAGLINE_CHAR_LIMIT:
            short_tagline_stores.append({
                'id': record['id'],
                'name': fields.get('店名', 'N/A'),
                'tagline': tagline,
                'tags': fields.get('シーンタグ', []),
                'menu': fields.get('メニュー', ''),
                'hours': fields.get('営業時間', ''),
                'description': fields.get('説明', '')
            })

    return short_tagline_stores

def generate_expansion(store_data, client):
    """Generate 35-char expansion of tagline using Claude API"""

    prompt = f"""以下の店舗情報から、35字以内の紹介文を作成してください。
捏造禁止。既存の一言メモを拡張する方向で。評価語なし。です/ます体は使わない。

店名: {store_data['name']}
既存一言: {store_data['tagline']}
タグ: {', '.join(store_data['tags']) if isinstance(store_data['tags'], list) else store_data['tags']}
メニュー: {store_data['menu']}
営業時間: {store_data['hours']}
説明: {store_data['description']}

35字以内の紹介文のみを返してください。説明や重複は不要です。"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        expansion = message.content[0].text.strip()

        # Verify character count
        if len(expansion) > EXPANSION_CHAR_LIMIT:
            # Try again with stronger emphasis on character limit
            prompt_strict = f"{prompt}\n\n重要: 必ず35字以内にしてください。"
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": prompt_strict
                    }
                ]
            )
            expansion = message.content[0].text.strip()

        return expansion if len(expansion) <= EXPANSION_CHAR_LIMIT else None
    except Exception as e:
        print(f"Error generating expansion for {store_data['name']}: {e}")
        return None

def process_stores(short_tagline_stores):
    """Process stores in batches and generate expansions"""
    if not CLAUDE_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    results = []

    total = len(short_tagline_stores)
    print(f"Processing {total} stores with taglines <= {TAGLINE_CHAR_LIMIT} characters...")

    for i, store in enumerate(short_tagline_stores, 1):
        expansion = generate_expansion(store, client)

        result = {
            'name': store['name'],
            'old_tagline': store['tagline'],
            'expansion': expansion,
            'char_count': len(expansion) if expansion else 0,
            'success': expansion is not None
        }
        results.append(result)

        status = "✓" if result['success'] else "✗"
        print(f"[{i}/{total}] {status} {store['name']}: {store['tagline']} → {expansion or '(failed)'}")

    return results

def generate_log_file(results, short_tagline_stores):
    """Generate markdown log file"""
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = f"logs/description_expansion_{timestamp}.md"

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    content = f"""# 一言メモ拡張レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## サマリー
- 処理対象: {len(short_tagline_stores)} 店舗
- 成功: {len(successful)} 件
- 失敗: {len(failed)} 件

## 拡張案一覧

| 店名 | 旧一言 | 新案 | 文字数 |
|------|--------|------|--------|
"""

    for result in results:
        if result['success']:
            content += f"| {result['name']} | {result['old_tagline']} | {result['expansion']} | {result['char_count']} |\n"

    if failed:
        content += f"\n## 失敗した店舗\n\n| 店名 | 旧一言 | 理由 |\n|------|--------|------|\n"
        for result in failed:
            content += f"| {result['name']} | {result['old_tagline']} | API エラー |\n"

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return log_file, len(successful), len(failed)

def main():
    """Main function"""
    print("=" * 60)
    print("一言メモ拡張スクリプト")
    print("=" * 60)

    # Fetch records
    print("\nAirtable からデータを取得中...")
    try:
        records = fetch_airtable_records()
        print(f"取得完了: {len(records)} 件")
    except Exception as e:
        print(f"Error fetching records: {e}")
        sys.exit(1)

    # Extract short tagline stores
    print("\n20字以下の一言メモを持つ店舗を抽出中...")
    short_tagline_stores = extract_short_tagline_stores(records)
    print(f"抽出完了: {len(short_tagline_stores)} 店舗")

    if not short_tagline_stores:
        print("対象となる店舗がありません")
        sys.exit(0)

    # Process stores
    print(f"\n拡張案を生成中 (最大 {len(short_tagline_stores)} 件)...")
    results = process_stores(short_tagline_stores)

    # Generate log
    print("\nログファイルを生成中...")
    log_file, success_count, fail_count = generate_log_file(results, short_tagline_stores)
    print(f"ログ出力: {log_file}")

    # Final report
    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"処理数: {len(short_tagline_stores)}")
    print(f"成功: {success_count}")
    print(f"失敗: {fail_count}")
    print(f"ログファイル: {log_file}")

if __name__ == '__main__':
    main()
