#!/usr/bin/env python3
"""
「食事なし」と判定された26件のレコードから「ランチあり」タグを削除
"""

import os
import requests
from pathlib import Path

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

SCENE_FIELD = "fldDl6OsS4EKmJT18"
STORE_NAME_FIELD = "fldpEdbx8RE5XfBln"

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 削除対象の店名（logs/lunch_judge_v2.txt から抽出）
remove_lunch_stores = {
    "小さな菓子工房 ひとてま",
    "pitu",
    "M cherie",
    "Kitchen RIZ(キッチンリズ)",
    "SWEETS SHOP 3o'clock",
    "ドトールコーヒーショップ 新潟古町通り七番町店",
    "cafe Lily(カフェリリー)",
    "ナチュール（Nature）",
    "午後からドルチェ",
    "ドトールコーヒーショップ DOUTOR st.CoCoLo新潟店",
    "3Rs（スリーアールズ）",
    "SEIKŌUKI(セイコウキ)",
    "アラモード・キムラ",
    "白根グレープガーデン(農園カフェ)",
    "ドトールコーヒーショップ 新潟万代シティ店",
    "Boulanger le coeur",
    "絲と糸 -いとといと-",
    "ドトールコーヒーショップ 新潟柾谷小路店",
    "jelicafe(ジェリカフェ)",
    "cafe HaRu-NiRe(ハルニレ)",
    "Nolla Mura",
    "奥阿賀グロッサリー combirie(コンビリー)",
    "703scone（ナオミスコーン）",
    "Seikōuki",
    "カフェ ブロッケン",
    "ドトールコーヒーショップ 長岡東口店"
}

print("=" * 80)
print("「ランチあり」タグ削除")
print("=" * 80)

# 全レコード取得
all_records = []
offset = None

print("\n【Step 1】全384件を取得中...")
while True:
    params = {"pageSize": 100, "returnFieldsByFieldId": "true"}
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

# 「ランチあり」が付いているレコードを抽出
print("【Step 2】削除対象のレコードを特定中...")

target_records = []
for record in all_records:
    fields = record.get('fields', {})
    store_name = fields.get(STORE_NAME_FIELD, '')
    tags = fields.get(SCENE_FIELD, [])

    if isinstance(tags, list) and "ランチあり" in tags and store_name in remove_lunch_stores:
        target_records.append({
            'id': record['id'],
            'name': store_name,
            'tags': tags.copy()
        })

print(f"削除対象: {len(target_records)} 件\n")

if len(target_records) != len(remove_lunch_stores):
    print(f"⚠️  警告: 削除対象の店舗数が一致しません")
    print(f"   期待値: {len(remove_lunch_stores)}, 実際: {len(target_records)}")
    print(f"   見つからない店舗:")
    found_names = {r['name'] for r in target_records}
    for name in remove_lunch_stores - found_names:
        print(f"   - {name}")
    exit(1)

# タグを削除
print("【Step 3】「ランチあり」タグを削除中...")

update_count = 0
for record in target_records:
    new_tags = [tag for tag in record['tags'] if tag != "ランチあり"]

    update_url = f"{url}/{record['id']}"
    update_data = {
        "fields": {
            SCENE_FIELD: new_tags
        }
    }

    response = requests.patch(update_url, json=update_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 更新エラー {record['name']}: {response.status_code}")
        print(f"   {response.text}")
        exit(1)

    update_count += 1
    if update_count % 10 == 0:
        print(f"  処理中: {update_count}/{len(target_records)}")

print(f"完了: {update_count} 件のレコードを更新しました\n")

# 5件を再取得して確認
print("【Step 4】書き込み確認（5件をランダムに再取得）...")

import random
sample_records = random.sample(target_records, min(5, len(target_records)))

for i, record in enumerate(sample_records, 1):
    verify_url = f"{url}/{record['id']}"
    response = requests.get(verify_url, headers=headers, params={"returnFieldsByFieldId": "true"})

    if response.status_code != 200:
        print(f"❌ 取得エラー: {response.status_code}")
        exit(1)

    data = response.json()
    fields = data.get('fields', {})
    current_tags = fields.get(SCENE_FIELD, [])

    lunch_removed = "ランチあり" not in current_tags
    other_tags_exist = len(current_tags) > 0 or len(record['tags']) == 1

    print(f"\n{i}. {record['name']}")
    print(f"   修正前タグ: {record['tags']}")
    print(f"   修正後タグ: {current_tags}")
    print(f"   ランチあり削除: {'✓' if lunch_removed else '✗'}")
    print(f"   他タグ保持: {'✓' if other_tags_exist or len(current_tags) > 0 else 'なし（正常）'}")

print("\n" + "=" * 80)
print(f"【完了】26件のレコードから「ランチあり」タグを削除しました")
print("=" * 80)
