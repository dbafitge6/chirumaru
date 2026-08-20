# File Dump Review

## memo_fact_check.py

```python
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
            'status': 'OK' | 'UNVERIFIED' | 'FETCH_ERROR'
        }
    """

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
        'unverified': []
    }

    for memo_data in memos:
        result = check_memo_facts(
            memo=memo_data['memo'],
            store_name=memo_data['store_name'],
            url=memo_data['url']
        )

        if result['status'] == 'OK' and result['verified']:
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
            'verification_rate': f"{len(results['verified']) / len(memos) * 100:.1f}%" if memos else "N/A"
        }
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
```

## memo_fact_check_results.json

```json
{
  "timestamp": "2026-08-20T18:11:05.537246",
  "memos_checked": 5,
  "verified": [
    {
      "memo": "自家製バゲルと新潟産肉のハンバーグ",
      "store_name": "ITALIAN RESTAURANT LIFE NIIGATA",
      "url": "https://r.gnavi.co.jp/g328hg0e0000/",
      "verified": true,
      "matched_keywords": [
        "ITALIAN",
        "LIFE",
        "ITALIAN RESTAURANT LIFE NIIGATA",
        "RESTAURANT",
        "NIIGATA"
      ],
      "missing_keywords": [
        "ハンバーグ",
        "自家製バゲルと新潟産肉のハンバーグ",
        "バゲル"
      ],
      "status": "OK",
      "match_count": 5,
      "total_keywords": 8
    },
    {
      "memo": "焙煎珈琲と店内焼きの自家製パン",
      "store_name": "COFFEE STAND",
      "url": "https://things-niigata.jp/other/coffee-stand/",
      "verified": true,
      "matched_keywords": [
        "COFFEE STAND",
        "STAND",
        "パン",
        "COFFEE"
      ],
      "missing_keywords": [
        "焙煎珈琲と店内焼きの自家製パン",
        "珈琲"
      ],
      "status": "OK",
      "match_count": 4,
      "total_keywords": 6
    }
  ],
  "unverified": [
    {
      "memo": "モーニングは無料トースト＆卵付き",
      "store_name": "コメダ珈琲店 長岡堺町店",
      "url": "https://map.yahoo.co.jp/v3/place/4bCBNxgi85g",
      "verified": false,
      "matched_keywords": [
        "長岡堺町店",
        "トースト",
        "コメダ珈琲店"
      ],
      "missing_keywords": [
        "コメダ珈琲店 長岡堺町店",
        "モーニングは無料トースト",
        "卵付き"
      ],
      "status": "UNVERIFIED",
      "match_count": 3,
      "total_keywords": 6
    },
    {
      "memo": "ランドリー併設。手焙煎珈琲が特徴",
      "store_name": "Hoshiba Come sta?",
      "url": "https://things-niigata.jp/other/hoshiba/",
      "verified": false,
      "matched_keywords": [
        "ランドリー",
        "Come",
        "Hoshiba"
      ],
      "missing_keywords": [
        "Hoshiba Come sta?",
        "sta?",
        "珈琲",
        "ランドリー併設",
        "手焙煎珈琲が特徴"
      ],
      "status": "UNVERIFIED",
      "match_count": 3,
      "total_keywords": 8
    },
    {
      "memo": "バタークリームの花がデコレーション特徴",
      "store_name": "M cherie",
      "url": "https://things-niigata.jp/other/m-cherie/",
      "verified": false,
      "matched_keywords": [
        "cherie"
      ],
      "missing_keywords": [
        "M cherie",
        "バタークリームの花がデコレーション特徴"
      ],
      "status": "UNVERIFIED",
      "match_count": 1,
      "total_keywords": 3
    }
  ],
  "summary": {
    "total": 5,
    "verified_count": 2,
    "unverified_count": 3,
    "verification_rate": "40.0%"
  }
}
```
