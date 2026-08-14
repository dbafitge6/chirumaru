#!/usr/bin/env python3
"""
Airtable シーンタグ更新スクリプト
営業時間フィールドから日曜営業・夜まで営業タグを判定し、Airtableに書き込む
"""

import os
import re
import requests
from datetime import datetime

# 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_NAME = "Stores"
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")

# フィールドID
BUSINESS_HOURS_FIELD = "fld1ulQZqD0lVLpmP"  # 営業時間
SCENE_FIELD = "fldDl6OsS4EKmJT18"  # シーン

if not AIRTABLE_TOKEN:
    print("❌ エラー: AIRTABLE_TOKEN 環境変数が設定されていません")
    exit(1)

# 日曜定休キーワード
SUNDAY_OFF_KEYWORDS = ["日曜定休", "日・祝定休", "日曜休", "日曜休館", "日曜休み", "毎週日曜休"]


def extract_closed_days(business_hours_text):
    """定休日を示す語（定休、休館など）と一緒に書かれている曜日を抽出"""
    if not business_hours_text:
        return None

    # 不定休は判定不能
    if "不定休" in business_hours_text:
        return None

    # 定休日ゼロ（無休、定休なし等）→ 「なし」を返す
    if any(kw in business_hours_text for kw in ["無休", "年中無休", "定休なし", "休みなし"]):
        return "なし"

    # 定休を示す語と一緒に書かれている曜日を正規表現で抽出
    closed_patterns = [
        r'定休日\s*[:：]\s*([月火水木金土日祝〜~、・\-\d第曜]+)',  # 「定休日: 火曜」形式
        r'([月火水木金土日祝〜~、・\-\d第曜]+?)(?:定休|休館|休業|休み)',  # 「月~木・日定休」形式
    ]

    for pattern in closed_patterns:
        matches = re.findall(pattern, business_hours_text)
        if matches:
            return matches[-1]

    # 定休を示す語がない → 判定不能
    return None


def get_closing_time(business_hours_text):
    """営業時間テキストから最後の閉店時刻を抽出（日跨ぎ対応）"""
    if not business_hours_text:
        return None

    # 日跨ぎ営業（「翌」を含む）の場合は late night と判定
    if "翌" in business_hours_text:
        return (24, 0)  # 深夜営業を示す特殊値

    # 時刻パターン：HH:MM または HH時MM分
    time_patterns = [
        r'(\d{1,2}):(\d{2})',  # HH:MM
        r'(\d{1,2})時(\d{2})分',  # HH時MM分
    ]

    times = []
    for pattern in time_patterns:
        matches = re.findall(pattern, business_hours_text)
        for match in matches:
            hour, minute = int(match[0]), int(match[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                times.append((hour, minute))

    if not times:
        return None

    return times[-1]


def is_sunday_open(business_hours_text):
    """日曜営業を判定"""
    if not business_hours_text:
        return None

    closed_days = extract_closed_days(business_hours_text)

    if closed_days is None:
        return None

    if closed_days == "なし":
        return True

    if "日" in closed_days:
        return False
    else:
        return True


def is_evening_open(business_hours_text):
    """夜まで営業を判定（19:00以降に営業、または日跨ぎ営業）"""
    closing_time = get_closing_time(business_hours_text)
    if not closing_time:
        return None

    hour, minute = closing_time
    if hour == 24:
        return True

    total_minutes = hour * 60 + minute
    nineteen_oclock = 19 * 60  # 19:00

    return total_minutes >= nineteen_oclock


def get_scene_tags(record_id, business_hours_text):
    """営業時間からシーンタグを判定"""
    tags = []

    sunday_open = is_sunday_open(business_hours_text)
    if sunday_open is True:
        tags.append("日曜営業")

    evening_open = is_evening_open(business_hours_text)
    if evening_open is True:
        tags.append("夜まで営業")

    return tags


# メイン処理
print("=" * 70)
print("🔄 Airtable シーンタグ更新開始")
print("=" * 70)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

all_records = []
offset = None

try:
    # すべてのレコードを取得
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

    print(f"✅ 取得完了: {len(all_records)} 件")

    # タグ判定と更新
    updated_count = 0
    for record in all_records:
        fields = record['fields']
        record_id = record['id']
        business_hours = fields.get(BUSINESS_HOURS_FIELD, '')

        tags = get_scene_tags(record_id, business_hours)

        if tags:
            # Airtable に更新
            update_url = f"{url}/{record_id}"
            update_data = {
                "fields": {
                    SCENE_FIELD: tags
                }
            }

            update_response = requests.patch(update_url, json=update_data, headers=headers)
            if update_response.status_code == 200:
                updated_count += 1
            else:
                print(f"⚠️  レコード {record_id} の更新失敗: {update_response.status_code}")

    print(f"\n✅ 書き込み完了: {updated_count} 件を更新")

except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ シーンタグ更新完了！")
print("=" * 70)
