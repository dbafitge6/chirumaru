#!/usr/bin/env python3
"""
Memo Enrichment Pipeline - Automatically generate store memos and tags from web research
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from anthropic import Anthropic

BASE_ID = 'appyyoKM7RprQRht8'
TABLE_ID = 'tblcOdcqCxzb7kX0e'
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
PROCESSED_FILE = os.path.join(LOGS_DIR, 'memo_enrichment_processed.json')
MAX_BATCH_SIZE = 30  # Process up to 30 shops per run

os.makedirs(LOGS_DIR, exist_ok=True)

def load_processed_records() -> set:
    """Load set of already processed record IDs"""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('processed_record_ids', []))
    return set()

def save_processed_records(record_ids: set):
    """Save processed record IDs"""
    with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'last_updated': datetime.now().isoformat(),
            'processed_record_ids': list(record_ids)
        }, f, ensure_ascii=False, indent=2)

def get_shops_needing_enrichment(token: str) -> List[Dict[str, Any]]:
    """Fetch shops with incomplete memos or tags from Airtable"""
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'

    all_records = []
    offset = None

    # Fetch all records with pagination
    print("Fetching all records from Airtable...")
    while True:
        params = {'pageSize': 100}
        if offset:
            params['offset'] = offset

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"Airtable API error: {response.status_code} {response.text}")

        data = response.json()
        if 'error' in data:
            raise RuntimeError(f"Airtable API error: {data['error']}")

        batch = data.get('records', [])
        all_records.extend(batch)
        print(f"  Fetched {len(batch)} records (total: {len(all_records)})")
        offset = data.get('offset')
        if not offset:
            break

    # Load previously processed record IDs
    processed = load_processed_records()
    print(f"Previously processed: {len(processed)} records")

    result = []

    for record in all_records:
        record_id = record['id']
        if record_id in processed:
            continue

        fields = record.get('fields', {})
        shop_name = fields.get('Store Name', 'Unknown')
        memo = fields.get('一言メモ', '').strip()
        tags = fields.get('タグ', '')
        website_url = fields.get('Website', '').strip()

        # Check if memo is short (< 20 chars) or empty
        # Tags filtering is skipped for now since memo is primary criterion
        memo_is_short = len(memo) < 20

        if not website_url:
            print(f"SKIPPED (no URL): {shop_name:30s} | ID: {record_id}")
            continue

        if memo_is_short:
            print(f"CANDIDATE: {shop_name:30s} | ID: {record_id} | memo_len={len(memo):2d} | memo='{memo}'")
            result.append(record)

        if len(result) >= MAX_BATCH_SIZE:
            print(f"Reached batch size limit ({MAX_BATCH_SIZE})")
            break

    print(f"\nTotal candidates for enrichment: {len(result)}")
    return result

def generate_memo(shop_name: str, area: str, menu_or_features: str, web_content: str) -> Optional[str]:
    """Generate a memo using Claude API"""
    print(f"[DEBUG] generate_memo called for: {shop_name}")
    client = Anthropic()

    prompt = f"""以下の情報から、ちるまるInstagram投稿用の一言メモを生成してください。

店舗情報:
- 店名: {shop_name}
- エリア: {area}
- メニュー/特徴: {menu_or_features}

Web検索結果:
{web_content[:1000]}

要件（CLAUDE.mdより）:
- 35字以内
- 「です」「ます」で終わらない
- 評価語（旨い、絶品、人気、おすすめ等）を使わない
- 語尾バリエーション：体言止め、「〜が名物」「〜特徴」など

例:
- 「直火焙煎コーヒーが特徴。温かみのある内装」（18字）
- 「シェアスペース内のカフェ」（11字）

必ず以下のように答えてください。考える必要はなく、即座にメモ候補を日本語で出力してください:

メモ候補（35字以内で、1つだけ）:"""

    try:
        response = client.messages.create(
            model='claude-opus-5',
            max_tokens=100,
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )

        # Extract text blocks (filter out thinking blocks)
        # ThinkingBlock objects don't have .text attribute, so filter by type
        print(f"[DEBUG] Response content blocks: {len(response.content)}")
        text_blocks = []
        for block in response.content:
            print(f"[DEBUG] Block type: {type(block)}, hasattr type: {hasattr(block, 'type')}")
            if hasattr(block, 'type'):
                print(f"[DEBUG] Block.type = {block.type}")
            if hasattr(block, 'type') and block.type == "text" and hasattr(block, 'text'):
                text_blocks.append(block.text)
        print(f"[DEBUG] Extracted {len(text_blocks)} text blocks")

        memo = "".join(text_blocks).strip()

        # Validate length and non-empty
        print(f"[DEBUG] Memo validation: len={len(memo)}, content='{memo}'")
        if len(memo) <= 35 and memo:
            print(f"[DEBUG] Memo valid, returning: {memo}")
            return memo
        else:
            if memo:
                print(f"[DEBUG] Memo too long ({len(memo)} chars): {memo[:50]}")
            else:
                print(f"[DEBUG] Memo is empty or None")
            return None
    except Exception as e:
        import traceback
        error_msg = f"Claude API error: {e}\nFull traceback:\n{traceback.format_exc()}"
        print(error_msg)  # stdout に出力（GitHub Actions で表示される）
        print(error_msg, file=sys.stderr)
        return None

def search_shop_info(shop_name: str) -> str:
    """Search for shop information (simplified version)"""
    # In production, use Google Search API or similar
    # For now, return placeholder
    return f"Search results for {shop_name}: [Information would come from web search]"

def verify_memo_with_fact_check(shop_name: str, memo: str, url: str) -> Dict[str, Any]:
    """Run fact-check on memo using memo_fact_check.py"""
    import tempfile

    test_data = [
        {
            'store_name': shop_name,
            'memo': memo,
            'url': url
        }
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f, ensure_ascii=False)
        temp_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), 'memo_fact_check.py'), temp_file],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                'status': 'ERROR',
                'error': result.stderr,
                'reason': f"Fact-check script error: {result.stderr[:100]}"
            }

        output = json.loads(result.stdout)

        # Extract verification result with consistent structure
        if output.get('verified'):
            fact_result = output['verified'][0] if output['verified'] else None
            return {
                'status': 'VERIFIED',
                'result': fact_result,
                'reason': f"Verified ({fact_result.get('match_count', 0)}/{fact_result.get('total_keywords', 0)} keywords)" if fact_result else "Verified"
            }
        elif output.get('skipped'):
            fact_result = output['skipped'][0] if output['skipped'] else None
            return {
                'status': 'SKIPPED',
                'result': fact_result,
                'reason': f"Skipped - {fact_result.get('reason', 'unknown reason')}" if fact_result else "Skipped"
            }
        elif output.get('unverified'):
            fact_result = output['unverified'][0] if output['unverified'] else None
            return {
                'status': 'UNVERIFIED',
                'result': fact_result,
                'reason': f"Unverified - {fact_result.get('status', 'unknown')} ({fact_result.get('match_count', 0)}/{fact_result.get('total_keywords', 0)} keywords)" if fact_result else "Unverified"
            }
        else:
            return {
                'status': 'SKIPPED',
                'reason': 'No verification data'
            }
    finally:
        os.unlink(temp_file)

def main():
    airtable_token = os.getenv('AIRTABLE_TOKEN')
    if not airtable_token:
        raise ValueError("AIRTABLE_TOKEN environment variable not set")

    # Fetch shops needing enrichment
    shops = get_shops_needing_enrichment(airtable_token)

    print(f"\n{'='*80}")
    print(f"Starting enrichment for {len(shops)} shops")
    print(f"{'='*80}\n")

    results = {
        'timestamp': datetime.now().isoformat(),
        'total_processed': len(shops),
        'verified': [],
        'unverified': [],
        'errors': []
    }

    processed_ids = load_processed_records()

    for idx, shop in enumerate(shops, 1):
        record_id = shop['id']
        fields = shop.get('fields', {})

        shop_name = fields.get('Store Name', 'Unknown')
        area = fields.get('Area', '')
        menu = fields.get('メニュー', '')
        website_url = fields.get('Website', '')

        print(f"\n[{idx}/{len(shops)}] Processing: {shop_name}")
        print(f"  Record ID: {record_id}")

        # Generate memo candidate
        web_content = search_shop_info(shop_name)
        memo_candidate = generate_memo(shop_name, area, menu, web_content)

        if not memo_candidate:
            print(f"  ❌ ERROR: Failed to generate memo")
            results['errors'].append({
                'record_id': record_id,
                'shop_name': shop_name,
                'error': 'Failed to generate memo'
            })
            processed_ids.add(record_id)
            continue

        print(f"  Generated: '{memo_candidate}' ({len(memo_candidate)} chars)")

        # Verify memo
        verification = verify_memo_with_fact_check(shop_name, memo_candidate, website_url or '')

        if verification['status'] == 'VERIFIED':
            print(f"  ✅ VERIFIED")
            results['verified'].append({
                'record_id': record_id,
                'shop_name': shop_name,
                'memo_candidate': memo_candidate,
                'source_url': website_url,
                'verification': verification['result']
            })
        else:
            reason = verification.get('reason', 'Unknown')
            print(f"  ⚠️  UNVERIFIED: {reason}")
            results['unverified'].append({
                'record_id': record_id,
                'shop_name': shop_name,
                'memo_candidate': memo_candidate,
                'source_url': website_url,
                'status': verification['status'],
                'reason': reason
            })

        processed_ids.add(record_id)

    # Save processed IDs (BEFORE writing logs)
    print(f"\n\nSaving {len(processed_ids)} processed record IDs...")
    save_processed_records(processed_ids)
    print(f"✅ Saved to {PROCESSED_FILE}")

    # Write results to markdown log
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(LOGS_DIR, f'memo_enrichment_{timestamp}.md')

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f'# Memo Enrichment Results\n\n')
        f.write(f'**Timestamp**: {results["timestamp"]}\n')
        f.write(f'**Total Processed**: {results["total_processed"]}\n')
        f.write(f'**Verified**: {len(results["verified"])}\n')
        f.write(f'**Unverified**: {len(results["unverified"])}\n')
        f.write(f'**Errors**: {len(results["errors"])}\n')
        f.write(f'**Processed IDs File**: {PROCESSED_FILE}\n\n')

        if results['verified']:
            f.write('## Verified Memos (Ready for Airtable)\n\n')
            for item in results['verified']:
                f.write(f'### {item["shop_name"]}\n')
                f.write(f'- **Record ID**: {item["record_id"]}\n')
                f.write(f'- **Memo**: `{item["memo_candidate"]}` ({len(item["memo_candidate"])} chars)\n')
                f.write(f'- **Source**: {item["source_url"]}\n')
                f.write(f'- **Verification**: {item["verification"]}\n\n')

        if results['unverified']:
            f.write('## Unverified Memos (Manual Review Needed)\n\n')
            for item in results['unverified']:
                f.write(f'### {item["shop_name"]}\n')
                f.write(f'- **Record ID**: {item["record_id"]}\n')
                f.write(f'- **Memo Candidate**: `{item["memo_candidate"]}` ({len(item["memo_candidate"])} chars)\n')
                f.write(f'- **Source**: {item["source_url"]}\n')
                f.write(f'- **Status**: {item["status"]}\n')
                f.write(f'- **Reason**: {item["reason"]}\n\n')

        if results['errors']:
            f.write('## Errors\n\n')
            for item in results['errors']:
                f.write(f'- **{item["shop_name"]}** (ID: {item["record_id"]}): {item["error"]}\n')

    # Save summary for GitHub Actions
    summary_file = os.path.join(LOGS_DIR, 'memo_enrichment_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': results['timestamp'],
            'total_processed': results['total_processed'],
            'verified_count': len(results['verified']),
            'unverified_count': len(results['unverified']),
            'error_count': len(results['errors']),
            'total_processed_ids': len(processed_ids)
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Results written to: {log_file}")
    print(f"📊 Summary: {summary_file}")

if __name__ == '__main__':
    main()
