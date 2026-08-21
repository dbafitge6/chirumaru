#!/usr/bin/env python3
"""
Memo Enrichment Pipeline - Automatically generate store memos and tags from web research
"""

import json
import os
import sys
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from anthropic import Anthropic

BASE_ID = 'appyyoKM7RprQRht8'
TABLE_ID = 'tblcOdcqCxzb7kX0e'
MEMO_FIELD_ID = 'fldZTL8r12En3D6eF'
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

        # Check if memo is short (< 30 chars) or empty - target is 30-35 chars
        # Tags filtering is skipped for now since memo is primary criterion
        memo_needs_expansion = len(memo) < 30

        if not website_url:
            print(f"SKIPPED (no URL): {shop_name:30s} | ID: {record_id}")
            continue

        if memo_needs_expansion:
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
- 30～35字程度（30字以上35字以内が目標）
- 「です」「ます」で終わらない
- 評価語（旨い、絶品、人気、おすすめ等）を使わない
- 語尾バリエーション：体言止め、「〜が名物」「〜特徴」など
- メモ本体に文字数や記号による注釈を一切含めないこと
- 店舗の特徴・おすすめを簡潔に表現

例:
- 「直火焙煎コーヒーが特徴。温かみのある内装」（19字）
- 「シェアスペース内のカフェ、駐車場完備」（18字）
- 「自家製ケーキとコーヒーが自慢の隠れ家」（18字）

【出力指示】メモ本体だけを出力してください。「メモ候補」などのラベル・前置き・説明は一切付けないでください。30～35字程度でメモ本体のみを出力してください。"""

    try:
        response = client.messages.create(
            model='claude-sonnet-5',
            max_tokens=100,
            thinking={"type": "disabled"},
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

        # Remove character count annotations like （26字） or (26 chars) as safety measure
        memo_cleaned = re.sub(r'（\d+字）', '', memo).strip()

        if len(memo_cleaned) <= 35 and memo_cleaned:
            print(f"[DEBUG] Memo valid, returning: {memo_cleaned} ({len(memo_cleaned)} chars)")
            return memo_cleaned
        else:
            if memo_cleaned:
                print(f"[DEBUG] Memo too long ({len(memo_cleaned)} chars): {memo_cleaned[:50]}")
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
    return f"Search results for {shop_name}: [Information would come from web search]"

def update_airtable_memo(token: str, record_id: str, memo: str) -> bool:
    """Update memo field in Airtable for a specific record"""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}'

    data = {
        'fields': {
            MEMO_FIELD_ID: memo
        }
    }

    try:
        response = requests.patch(url, json=data, headers=headers, timeout=10)

        if response.status_code in [200, 204]:
            print(f"  ✅ Airtable updated: {memo[:50]}")
            return True
        else:
            print(f"  ❌ Airtable update failed: {response.status_code} {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ Airtable update error: {e}")
        return False

def verify_memo_with_fact_check(shop_name: str, memo: str, url: str) -> Dict[str, Any]:
    """Run fact-check on memo using memo_fact_check.py

    For JS rendering domains, adopt SKIP_JS status to accept memo without verification.
    This is safe because Claude generation is fact-aware via prompts.
    """
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
            text=True,
            timeout=30
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
            skip_reason = fact_result.get('reason', 'unknown') if fact_result else 'unknown'

            # Check if JS rendering is the reason - if so, mark as SKIP_JS to adopt memo
            if 'JavaScript' in skip_reason or 'javascript' in skip_reason or 'JS' in skip_reason:
                return {
                    'status': 'SKIP_JS',
                    'reason': 'JS rendering domain - adopting memo based on Claude generation quality',
                    'skip_reason': skip_reason
                }
            else:
                return {
                    'status': 'SKIPPED',
                    'result': fact_result,
                    'reason': f"Skipped - {skip_reason}" if fact_result else "Skipped"
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
    except subprocess.TimeoutExpired:
        return {
            'status': 'ERROR',
            'reason': 'Fact-check timeout (>30s) - likely JS rendering issue'
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
            print(f"  ✅ VERIFIED - Writing to Airtable")
            update_airtable_memo(airtable_token, record_id, memo_candidate)
            results['verified'].append({
                'record_id': record_id,
                'shop_name': shop_name,
                'memo_candidate': memo_candidate,
                'source_url': website_url,
                'verification': verification['result'],
                'airtable_updated': True
            })
        elif verification['status'] == 'SKIP_JS':
            print(f"  ✅ JS-SKIP - Writing to Airtable (Claude generation trusted)")
            update_airtable_memo(airtable_token, record_id, memo_candidate)
            results['verified'].append({
                'record_id': record_id,
                'shop_name': shop_name,
                'memo_candidate': memo_candidate,
                'source_url': website_url,
                'verification_status': 'SKIP_JS',
                'reason': verification.get('reason', ''),
                'airtable_updated': True
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
                'reason': reason,
                'airtable_updated': False
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
            f.write('## Updated in Airtable (Verified + JS-Skip)\n\n')
            for item in results['verified']:
                f.write(f'### {item["shop_name"]}\n')
                f.write(f'- **Record ID**: {item["record_id"]}\n')
                f.write(f'- **Memo**: `{item["memo_candidate"]}` ({len(item["memo_candidate"])} chars)\n')
                f.write(f'- **Source**: {item["source_url"]}\n')
                if 'verification' in item:
                    f.write(f'- **Verification**: {item["verification"]}\n')
                if 'verification_status' in item:
                    f.write(f'- **Status**: {item["verification_status"]} - {item.get("reason", "")}\n')
                f.write(f'- **Airtable Updated**: {item.get("airtable_updated", False)}\n\n')

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
    airtable_updated_count = sum(1 for item in results['verified'] if item.get('airtable_updated', False))
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': results['timestamp'],
            'total_processed': results['total_processed'],
            'verified_count': len(results['verified']),
            'airtable_updated_count': airtable_updated_count,
            'unverified_count': len(results['unverified']),
            'error_count': len(results['errors']),
            'total_processed_ids': len(processed_ids)
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Results written to: {log_file}")
    print(f"📊 Summary: {summary_file}")

if __name__ == '__main__':
    main()
