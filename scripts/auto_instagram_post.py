#!/usr/bin/env python3
"""
ちるまる Instagram 自動投稿システム
2日ごとに店舗を選択 → 動画生成 → 投稿
"""

import os
import json
import random
import subprocess
from pathlib import Path
from datetime import datetime
from instagrapi import Client
import requests

# 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_NAME = "Stores"
API_TOKEN = os.environ.get("AIRTABLE_TOKEN")
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")

if not all([API_TOKEN, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD]):
    print("❌ エラー: GitHub Secrets が設定されていません")
    print("   AIRTABLE_TOKEN, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD を設定してください")
    exit(1)

OUTPUT_DIR = Path("/Users/kobayashikazuya/chirumaru-repo/generated_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = OUTPUT_DIR / "instagram_post_history.json"
FRANCHISE_CHAINS = ['ドトール', 'タリーズ', 'スターバックス', 'コメダ']

print("=" * 70)
print("🎬 Instagram 自動投稿システム開始")
print("=" * 70)

# Step 1: Airtable から店舗を選択
print("\n【Step 1】Airtable から店舗を選択")
print("=" * 70)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

all_records = []
offset = None

try:
    while True:
        params = {} if not offset else {"offset": offset}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ API エラー: {response.status_code}")
            exit(1)

        data = response.json()
        all_records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset:
            break

    print(f"✅ 取得完了: {len(all_records)} 店舗")

    # フランチャイズ除外
    shops_list = []
    for record in all_records:
        fields = record.get('fields', {})
        name = fields.get('Store Name', 'Unknown')
        is_franchise = any(chain in name for chain in FRANCHISE_CHAINS)

        if not is_franchise:
            shops_list.append({
                'id': record['id'],
                'name': name,
                'area': fields.get('Area', 'Unknown'),
                'tags': fields.get('Tags', '').split(',')[0] if fields.get('Tags') else 'Unknown'
            })

    print(f"✅ フランチャイズ除外: {len(shops_list)} 店舗")

    # 前回選んだ店舗を除外
    selected_history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
            selected_history = history.get('last_3_shops', [])

    available_shops = [s for s in shops_list if s['name'] not in selected_history]
    selected_3 = random.sample(available_shops, min(3, len(available_shops)))

    print(f"\n🎯 今回選択した 3 店舗:")
    for i, shop in enumerate(selected_3, 1):
        print(f"  {i}. {shop['name']} - {shop['area']}")

    # 履歴を保存
    history = {
        'timestamp': datetime.now().isoformat(),
        'last_3_shops': [s['name'] for s in selected_3]
    }
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)

# Step 2: 動画を生成（簡易版）
print("\n【Step 2】動画を生成")
print("=" * 70)

# 前回作成した動画を再利用
video_path = OUTPUT_DIR / "test_reels.mp4"
if not video_path.exists():
    print(f"❌ 動画ファイルが見つかりません: {video_path}")
    print("   最初に video を手動で生成してください")
    exit(1)

print(f"✅ 動画ファイル確認: {video_path}")

# Step 3: Instagram に投稿
print("\n【Step 3】Instagram に投稿")
print("=" * 70)

try:
    print(f"📱 Instagram にログイン中...")
    cl = Client()
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    print(f"✅ ログイン成功")

    # キャプション作成
    shops_text = "\n".join([f"{i+1}. {s['name']} ({s['area']})" for i, s in enumerate(selected_3)])
    caption = f"""🌟 新潟のカフェ探し、今週の 3 店舗 🌟

{shops_text}

ちるまるにいがたで毎週新しいお店を紹介🎉
気になったお店があれば、ぜひ訪れてみてください☕

📸 @chiru_maru_

#新潟 #新潟カフェ #新潟グルメ #カフェ好きさんと繋がりたい #隠れ家カフェ"""

    print(f"\n📝 キャプション:")
    print(caption)

    # 投稿
    print(f"\n📤 投稿中...")
    media = cl.clip_upload(path=str(video_path), caption=caption)

    print(f"✅ 投稿成功！")
    print(f"   Post ID: {media.id}")
    print(f"   URL: https://www.instagram.com/p/{media.code}/")

except Exception as e:
    print(f"❌ Instagram 投稿エラー: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ 自動投稿完了！")
print("=" * 70)
