#!/usr/bin/env python3
"""
ちるまる Instagram 自動投稿システム
22日ごとに店舗を選択 → Postiz経由で投稿
"""

import os
import json
import random
import subprocess
from pathlib import Path
from datetime import datetime
import requests

# 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_NAME = "Stores"
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
POSTIZ_API_KEY = os.environ.get("POSTIZ_API_KEY")
INSTAGRAM_INTEGRATION_ID = "cmsopxrcz024opo0ygfgl0m4q"
VIDEO_URL = "https://uploads.postiz.com/Dw9DWadyRH.mp4"

if not all([AIRTABLE_TOKEN, POSTIZ_API_KEY]):
    print("❌ エラー: 環境変数が設定されていません")
    print("   AIRTABLE_TOKEN, POSTIZ_API_KEY を設定してください")
    exit(1)

OUTPUT_DIR = Path(__file__).parent.parent / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = OUTPUT_DIR / "instagram_post_history.json"
FRANCHISE_CHAINS = ['ドトール', 'タリーズ', 'スターバックス', 'コメダ']

# 誤字辞書
TYPO_MAP = {
    '情緒い': '情緒あ',
    '穿場': '穴場',
    '弌彦': '弥彦',
}

def fix_typos(text):
    """テキストから誤字を修正"""
    for typo, correct in TYPO_MAP.items():
        text = text.replace(typo, correct)
    return text

print("=" * 70)
print("🎬 Instagram 自動投稿システム開始")
print("=" * 70)

# Step 1: Airtable から店舗を選択
print("\n【Step 1】Airtable から店舗を選択")
print("=" * 70)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

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
                'description': fields.get('Description', '')
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

# Step 2: キャプション作成（誤字修正含む）
print("\n【Step 2】キャプション作成")
print("=" * 70)

caption_lines = [
    "🌟 新潟のカフェ探し 🌟",
    "",
]
for i, s in enumerate(selected_3, 1):
    caption_lines.append(f"{s['name']}")
    caption_lines.append(f"📍 {s['area']}")
    if s['description']:
        desc = fix_typos(s['description'])
        caption_lines.append(f"{desc}")
    caption_lines.append("")

caption_lines.extend([
    "ちるまるで毎日新しいお店を紹介🎉",
    "気になったお店があれば、ぜひ訪れてみてください☕",
    "",
    "📸 @chiru_maru_",
    "",
    "#新潟 #新潟カフェ #新潟グルメ #カフェ好きさんと繋がりたい #隠れ家カフェ #chirumaru"
])

caption = "\n".join(caption_lines)
caption = fix_typos(caption)

print(f"\n📝 キャプション:")
print(caption)

# Step 3: Postiz で投稿
print("\n【Step 3】Postiz で投稿")
print("=" * 70)

try:
    # Postiz API で投稿作成
    postiz_cmd = [
        'postiz', 'posts:create',
        '-c', caption,
        '-m', VIDEO_URL,
        '-s', datetime.utcnow().isoformat() + 'Z',
        '--settings', '{"post_type":"post"}',
        '-i', INSTAGRAM_INTEGRATION_ID
    ]

    result = subprocess.run(postiz_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ 投稿成功！")
        print(result.stdout)
    else:
        print(f"❌ Postiz エラー: {result.stderr}")
        exit(1)

except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ 自動投稿完了！")
print("=" * 70)
