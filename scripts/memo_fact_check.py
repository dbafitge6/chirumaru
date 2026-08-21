#!/usr/bin/env python3
"""
Fact-check memo against source URL content.

Validates that memo claims (store name, location, features) are actually present
in the source URL content using keyword matching.
"""

import json
import sys
import requests
from typing import Dict, List, Any
from urllib.parse import urlparse

JS_RENDER_DOMAINS = {
    'komeda.co.jp',
    'tullys.co.jp',
}

def extract_keywords(memo: str, store_name: str) -> List[str]:
    """Extract keywords from memo for verification."""
    keywords = [store_name]

    # Split store name into parts (e.g., "コメダ珈琲店 長岡堺町店" -> ["コメダ", "珈琲", "長岡", "堺町"])
    name_parts = store_name.replace('（', ' ').replace('）', ' ').replace('　', ' ').split()
    for part in name_parts:
        if len(part) >= 2:
            keywords.append(part)

    # Extract key words from memo (simplified chunking)
    import re
    # Remove punctuation and split
    text = memo.replace('。', ' ').replace('、', ' ').replace('＆', ' ')

    # Find sequences of 2+ characters
    chunks = re.findall(r'[぀-ゟ゠-ヿ一-鿿]+', text)

    for chunk in chunks:
        if len(chunk) >= 2:
            keywords.append(chunk)

    # Add individual important words (2-3 chars)
    important_words = ['珈琲', 'パン', 'ケーキ', 'サンド', 'トースト', 'ラーメン', 'コーヒー',
                      'ランドリー', 'カフェ', 'レストラン', 'バゲル', 'ハンバーグ']
    for word in important_words:
        if word in memo:
            keywords.append(word)

    return list(set([k for k in keywords if k]))

def fetch_url_content(url: str) -> str:
    """Fetch URL content with timeout."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"FETCH_ERROR: {str(e)}"

def check_memo_facts(memo: str, store_name: str, url: str) -> Dict[str, Any]:
    """
    Verify memo facts against URL content.

    Returns:
        {
            'memo': str,
            'store_name': str,
            'url': str,
            'verified': bool,
            'matched_keywords': List[str],
            'missing_keywords': List[str],
            'status': 'OK' | 'UNVERIFIED' | 'FETCH_ERROR' | 'SKIPPED'
        }
    """

    # Check if domain uses JavaScript rendering (not verifiable via requests)
    if url:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]

        if domain in JS_RENDER_DOMAINS:
            return {
                'memo': memo,
                'store_name': store_name,
                'url': url,
                'verified': None,
                'matched_keywords': [],
                'missing_keywords': [],
                'status': 'SKIPPED',
                'reason': 'Domain uses JavaScript rendering (not verifiable via requests)'
            }

    # Fetch content
    content = fetch_url_content(url)

    if content.startswith('FETCH_ERROR'):
        return {
            'memo': memo,
            'store_name': store_name,
            'url': url,
            'verified': False,
            'matched_keywords': [],
            'missing_keywords': [store_name],
            'status': 'FETCH_ERROR',
            'error': content
        }

    # Extract keywords to verify
    keywords = extract_keywords(memo, store_name)

    # Check which keywords appear in content
    matched = []
    missing = []

    for keyword in keywords:
        if keyword in content:
            matched.append(keyword)
        else:
            missing.append(keyword)

    # Verify: at least store name + at least one feature must match
    verified = (store_name in matched) and len(matched) > 1

    return {
        'memo': memo,
        'store_name': store_name,
        'url': url,
        'verified': verified,
        'matched_keywords': matched,
        'missing_keywords': missing,
        'status': 'OK' if verified else 'UNVERIFIED',
        'match_count': len(matched),
        'total_keywords': len(keywords)
    }

def main():
    """Process memo verification from JSON input."""
    if len(sys.argv) < 2:
        print("Usage: memo_fact_check.py <json_file>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            memos = json.load(f)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    # Process each memo
    results = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'memos_checked': len(memos),
        'verified': [],
        'unverified': [],
        'skipped': []
    }

    for memo_data in memos:
        result = check_memo_facts(
            memo=memo_data['memo'],
            store_name=memo_data['store_name'],
            url=memo_data['url']
        )

        if result['status'] == 'SKIPPED':
            results['skipped'].append(result)
        elif result['status'] == 'OK' and result['verified']:
            results['verified'].append(result)
        else:
            results['unverified'].append(result)

    # Output results
    output = {
        **results,
        'summary': {
            'total': len(memos),
            'verified_count': len(results['verified']),
            'unverified_count': len(results['unverified']),
            'skipped_count': len(results['skipped']),
            'verification_rate': f"{len(results['verified']) / len(memos) * 100:.1f}%" if memos else "N/A"
        }
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
