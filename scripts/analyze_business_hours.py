#!/usr/bin/env python3
"""
Airtable 営業時間解析スクリプト
営業時間フィールドから「日曜営業」「夜まで営業」タグを判定
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
    # パターン例：「月~木・日定休」「木・日・祝日定休」「火曜・第4水曜休館」「定休日: 火曜」
    closed_patterns = [
        r'定休日\s*[:：]\s*([月火水木金土日祝〜~、・\-\d第曜]+)',  # 「定休日: 火曜」形式
        r'([月火水木金土日祝〜~、・\-\d第曜]+?)(?:定休|休館|休業|休み)',  # 「月~木・日定休」形式
    ]

    for pattern in closed_patterns:
        matches = re.findall(pattern, business_hours_text)
        if matches:
            # 抽出した定休日の記載を返す（最後の部分を使用）
            return matches[-1]

    # 定休を示す語がない → 判定不能
    return None


def is_sunday_open(business_hours_text):
    """
    日曜営業を判定
    - 定休日ゼロ（無休、定休なし等） → 日曜営業（True）
    - 定休日の記載に「日」が含まれる → 日曜定休 → タグなし（False）
    - 定休日の記載があり「日」が含まれない → 日曜営業 → タグ付与（True）
    - 定休日の記載なし or「不定休」 → 判定不能 → タグなし（None）
    """
    if not business_hours_text:
        return None

    # 定休日を抽出
    closed_days = extract_closed_days(business_hours_text)

    if closed_days is None:
        # 定休日の記載がない or「不定休」 → 判定不能
        return None

    # 定休日ゼロ（無休、定休なし等）→ 日曜営業
    if closed_days == "なし":
        return True

    # 抽出した定休日に「日」が含まれるか確認
    if "日" in closed_days:
        # 日曜定休 → タグなし
        return False
    else:
        # 日曜営業 → タグ付与
        return True

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

    # 最後の時刻を返す（通常は閉店時刻）
    return times[-1]

def is_evening_open(business_hours_text):
    """夜まで営業を判定（19:00以降に営業、または日跨ぎ営業）"""
    closing_time = get_closing_time(business_hours_text)
    if not closing_time:
        return None

    hour, minute = closing_time
    # 深夜営業（翌営業の特殊値）
    if hour == 24:
        return True

    total_minutes = hour * 60 + minute
    nineteen_oclock = 19 * 60  # 19:00

    return total_minutes >= nineteen_oclock

def analyze_business_hours(record_id, shop_name, business_hours_text):
    """営業時間を解析して、タグを判定"""
    results = {
        'record_id': record_id,
        'shop_name': shop_name,
        'business_hours': business_hours_text,
        'closed_days': extract_closed_days(business_hours_text),
        'tags': [],
        'reasoning': []
    }

    # 日曜営業チェック
    sunday_open = is_sunday_open(business_hours_text)
    if sunday_open is True:
        results['tags'].append('日曜営業')
        if results['closed_days'] == 'なし':
            results['reasoning'].append('定休日: なし（無休/定休なし） → 日曜営業')
        else:
            results['reasoning'].append(f'定休日: {results["closed_days"]} (日を含まず) → 日曜営業')
    elif sunday_open is False:
        results['reasoning'].append(f'定休日: {results["closed_days"]} (日を含む) → 日曜営業なし')
    else:
        results['reasoning'].append('定休日記載なし or 不定休 → 判定不可（タグなし）')

    # 夜まで営業チェック
    evening_open = is_evening_open(business_hours_text)
    if evening_open is True:
        results['tags'].append('夜まで営業')
        closing_time = get_closing_time(business_hours_text)
        if closing_time[0] == 24:
            results['reasoning'].append('日跨ぎ営業（翌営業） → 夜まで営業と判定')
        else:
            results['reasoning'].append(f'閉店時刻 {closing_time[0]:02d}:{closing_time[1]:02d} (19:00以降) → 夜まで営業と判定')
    elif evening_open is False:
        closing_time = get_closing_time(business_hours_text)
        if closing_time:
            results['reasoning'].append(f'閉店時刻 {closing_time[0]:02d}:{closing_time[1]:02d} (19:00前) → 夜まで営業なし')
        else:
            results['reasoning'].append('営業時間情報なし')
    else:
        results['reasoning'].append('営業時間情報なし')

    return results

# メイン処理
print("=" * 70)
print("🔍 Airtable 営業時間解析（最初の20件）")
print("=" * 70)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

all_records = []
offset = None

try:
    # Airtable から20件取得
    while len(all_records) < 20:
        params = {
            "pageSize": min(100, 20 - len(all_records)),
            "returnFieldsByFieldId": "true"
        }
        if offset:
            params["offset"] = offset

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"❌ API エラー: {response.status_code}")
            exit(1)

        data = response.json()
        all_records.extend(data.get('records', []))
        offset = data.get('offset')

        if not offset or len(all_records) >= 20:
            break

    all_records = all_records[:20]
    print(f"✅ {len(all_records)} 件取得完了\n")

    # 解析結果
    results = []
    for record in all_records:
        fields = record.get('fields', {})
        record_id = record['id']
        shop_name = fields.get('fldpEdbx8RE5XfBln', 'Unknown')  # Store Name field ID
        business_hours = fields.get(BUSINESS_HOURS_FIELD, '')

        result = analyze_business_hours(record_id, shop_name, business_hours)
        results.append(result)

    # 結果表示（全件の原文を表示）
    print("\n【判定結果（全20件）】")
    print("=" * 120)
    for i, result in enumerate(results, 1):
        shop_name = result['shop_name']
        business_hours = result['business_hours']
        closed_days = result['closed_days'] if result['closed_days'] else '（記載なし）'
        tags = ', '.join(result['tags']) if result['tags'] else '（なし）'
        reasoning = ' | '.join(result['reasoning'])

        print(f"\n{i:2d}. {shop_name}")
        print(f"    営業時間: {business_hours}")
        print(f"    抽出定休日: {closed_days}")
        print(f"    タグ: {tags}")
        print(f"    根拠: {reasoning}")

    # 統計
    sunday_count = sum(1 for r in results if '日曜営業' in r['tags'])
    evening_count = sum(1 for r in results if '夜まで営業' in r['tags'])

    print(f"\n【統計】")
    print("=" * 70)
    print(f"日曜営業: {sunday_count}件")
    print(f"夜まで営業: {evening_count}件")
    print(f"両方: {sum(1 for r in results if len(r['tags']) == 2)}件")
    print(f"どちらでもない: {sum(1 for r in results if len(r['tags']) == 0)}件")

    print(f"\n⚠️  Airtable への書き込みは実行していません")
    print("確認後に、以下のコマンドで本実行してください:")
    print("python scripts/update_business_hours_tags.py")

except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)
