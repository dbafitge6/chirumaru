#!/usr/bin/env python3
"""
既存タグの出現回数を集計し、上位40件を表示
"""

import os
import requests
from pathlib import Path
from collections import Counter

# .env ファイルを読み込む
env_file = Path(__file__).parent.parent / ".env"
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
TAG_FIELD = "fldsh2ess7aYHhJ8e"  # 既存タグ

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 全レコード取得
print("=" * 80)
print("既存タグの集計")
print("=" * 80)

all_records = []
offset = None

print("\n【Step 1】全レコードを取得中...")
while True:
    params = {"returnFieldsByFieldId": "true"}
    if offset:
        params["offset"] = offset

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"❌ API エラー: {response.status_code}")
        exit(1)

    data = response.json()
    all_records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break

print(f"取得完了: {len(all_records)} 件\n")

# タグを抽出・分割
print("【Step 2】タグを抽出・分割中...")
all_tags = []
for record in all_records:
    fields = record.get('fields', {})
    tags_str = fields.get(TAG_FIELD, '')

    if tags_str:
        # "/" で分割
        tags = [tag.strip() for tag in tags_str.split('/') if tag.strip()]
        all_tags.extend(tags)

print(f"抽出完了: {len(all_tags)} 個のタグ\n")

# 出現回数を集計
tag_counts = Counter(all_tags)
sorted_tags = tag_counts.most_common()

print("【Step 3】集計結果（全件）\n")
print(f"ユニークタグ: {len(tag_counts)} 個\n")

# 全件を出力（後で判定用）
print("【全件一覧】")
print("=" * 80)
for i, (tag, count) in enumerate(sorted_tags, 1):
    # 出現回数が3以上を目安に、名物カテゴリの可能性を示す
    category_mark = ""
    if count >= 3:
        # 業態・設備と思われるキーワード
        exclude_keywords = [
            "カフェ", "パン屋", "喫茶", "スイーツ", "パティスリー",
            "ジェラート", "アイス", "駐車場", "テラス", "個室",
            "WiFi", "電源", "モーニング", "ランチ", "ディナー",
            "ペット", "子連れ", "喫煙", "禁煙"
        ]

        is_exclude = any(keyword in tag for keyword in exclude_keywords)
        if not is_exclude:
            category_mark = " ★ 名物候補"

    print(f"{i:3d}. {tag:<30s} / {count:3d}{category_mark}")

print("\n" + "=" * 80)
print(f"【上位40件抜粋】")
print("=" * 80)
for i, (tag, count) in enumerate(sorted_tags[:40], 1):
    category_mark = ""
    if count >= 3:
        exclude_keywords = [
            "カフェ", "パン屋", "喫茶", "スイーツ", "パティスリー",
            "ジェラート", "アイス", "駐車場", "テラス", "個室",
            "WiFi", "電源", "モーニング", "ランチ", "ディナー",
            "ペット", "子連れ", "喫煙", "禁煙"
        ]

        is_exclude = any(keyword in tag for keyword in exclude_keywords)
        if not is_exclude:
            category_mark = " ★"

    print(f"{i:2d}. {tag:<30s} / {count:3d}{category_mark}")

print("\n" + "=" * 80)
print(f"集計完了")
print("=" * 80)
