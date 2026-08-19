#!/usr/bin/env python3
"""
Airtable から記事作成用のデータを取得するスクリプト
"""

import os
import sys
from pathlib import Path
import requests

# .env ファイルを読み込む（auto_instagram_post.py と同じ方式）
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# トークン取得
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")

# トークンが取得できない場合は例外を投げて中止
if not AIRTABLE_TOKEN:
    print("ERROR: AIRTABLE_TOKEN が .env から取得できません")
    print("確認: .env ファイルに AIRTABLE_TOKEN が設定されているか確認してください")
    sys.exit(1)

print(f"✓ AIRTABLE_TOKEN を取得しました（{'*' * 10}）")

# Airtable 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_ID = "tblcOdcqCxzb7kX0e"

headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

# すべてのレコードを取得
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
all_records = []
offset = None

print("\n📥 Airtable からデータを取得中...")

while True:
    params = {}
    if offset:
        params["offset"] = offset

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"ERROR: API リクエスト失敗 ({response.status_code})")
        print(response.text)
        sys.exit(1)

    data = response.json()
    all_records.extend(data.get("records", []))

    offset = data.get("offset")
    if not offset:
        break

print(f"✓ 全レコード取得完了: {len(all_records)}件\n")

# 日曜営業タグを持つ店舗を抽出
sunday_open = []
for record in all_records:
    fields = record.get("fields", {})
    tags = fields.get("シーンタグ", [])

    if "日曜営業" in tags:
        sunday_open.append({
            "id": record.get("id"),
            "name": fields.get("店名", ""),
            "area": fields.get("エリア", ""),
            "business_hours": fields.get("営業時間", ""),
            "memo": fields.get("一言", ""),
            "tags": tags,
        })

# エリア順でソート
sunday_open.sort(key=lambda x: x["area"] or "")

# 結果表示
print("=" * 80)
print(f"📊 日曜営業タグを持つ店舗: {len(sunday_open)}件")
print("=" * 80)

# 最初の5件を詳しく表示
print("\n【最初の5件】\n")
for i, shop in enumerate(sunday_open[:5], 1):
    print(f"{i}. {shop['name']}")
    print(f"   ID: {shop['id']}")
    print(f"   エリア: {shop['area']}")
    print(f"   営業時間: {shop['business_hours']}")
    print(f"   一言: {shop['memo']}")
    print(f"   タグ: {', '.join(shop['tags'])}")
    print()

print("=" * 80)
print(f"\n✓ データ取得成功。記事作成に進めます。")
print(f"✓ 全 {len(sunday_open)} 件のデータが利用可能です。")
