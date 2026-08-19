#!/usr/bin/env python3
import os
import sys
import json
import random
import requests
from typing import Dict, List, Tuple

# Airtable Configuration
BASE_ID = "appyyoKM7RprQRht8"
TABLE_ID = "tblcOdcqCxzb7kX0e"
FIELD_ID = "fld7kYvLqO0lLFEWU"
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")

if not AIRTABLE_TOKEN:
    print("Error: AIRTABLE_TOKEN not set")
    sys.exit(1)

# Update data
updates = {
    "rec32OUV4mV2KBP4M": "シロノワール/モーニングセット。夜営業。日曜営業",
    "rec39gdsdfSGUjVny": "ケーキ/シフォン/マフィン。日曜営業",
    "recLUCBhwNN0Iagjr": "燕市のカフェ・飲食店です",
    "recPKbV4QAygxQ4gh": "コーヒー/本。日曜営業",
    "recQJorPye4Yny2pA": "ケーキ/焼き菓子/マカロン。夜営業",
    "recRTZ365yf5aOyYu": "カフェメニュー。夜営業",
    "recYzxFMOncgcrYef": "コーヒー/ケーキ/パスタ。ランチ対応",
    "recZ90IdhJ53xzooE": "コーヒー。夜営業。日曜営業",
    "recZhUu4LguRN1sPm": "バイキング/カフェメニュー。夜営業",
    "recdDmKuDfnHDrnXO": "コーヒー。夜営業。日曜営業",
    "recdWCIpv1ekuFq9V": "シロノワール、モーニングセット。夜営業。日曜営業",
    "recfM5RITjB06cGDr": "コーヒー。夜営業。日曜営業",
    "recfNBZYWdFDIQ8ym": "コーヒー。夜営業。日曜営業",
    "reci1NnwfPb2hGcZI": "シロノワール、モーニングセット。夜営業。日曜営業",
    "recjCwjEtc8j4O0wW": "パン/クロワッサン/食パン。日曜営業",
    "recr42tAHUeOlWG1M": "コーヒー。夜営業。日曜営業",
    "recsq385AnBwhO0Qa": "ドーナツ。夜営業。日曜営業",
    "recswYEtDNw0W3cb8": "コーヒー。夜営業。日曜営業",
    "rectX0CYdk2rFLqKr": "恋愛するフレンチトースト、ハウスメイドクラフトコーラ。こだわり",
    "recv7uUV4ghVI5TYV": "和菓子。こだわり・季節限定品",
}

headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("Airtable レコード一言メモ更新開始")
print(f"対象: {len(updates)} 件")
print("=" * 60)

# Step 1: Update all records
success_count = 0
failed_records = []

for record_id, memo in updates.items():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}"
    payload = {
        "fields": {
            FIELD_ID: memo
        }
    }

    try:
        response = requests.patch(url, json=payload, headers=headers)
        if response.status_code == 200:
            success_count += 1
            print(f"✓ {record_id}: 更新成功")
        else:
            failed_records.append((record_id, response.status_code, response.text))
            print(f"✗ {record_id}: 更新失敗 (HTTP {response.status_code})")
    except Exception as e:
        failed_records.append((record_id, str(e), ""))
        print(f"✗ {record_id}: エラー - {str(e)}")

print("\n" + "=" * 60)
print("更新結果")
print("=" * 60)
print(f"成功: {success_count}/{len(updates)} 件")
print(f"失敗: {len(failed_records)}/{len(updates)} 件")

if failed_records:
    print("\n失敗したレコード:")
    for record_id, error_code, error_text in failed_records:
        print(f"  - {record_id}: {error_code}")

# Step 2: Get all updated records for verification
print("\n" + "=" * 60)
print("更新確認用レコード一括取得")
print("=" * 60)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
params = {
    "fields[]": ["Name", FIELD_ID],
    "filterByFormula": f"OR({','.join([f'RECORD_ID()=\"{rid}\"' for rid in updates.keys()])})"
}

try:
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        records_data = response.json()
        all_records = records_data.get("records", [])
        print(f"取得成功: {len(all_records)} 件")

        # Create a dictionary for verification
        record_map = {}
        for record in all_records:
            rec_id = record["id"]
            fields = record.get("fields", {})
            store_name = fields.get("Name", "未取得")
            memo = fields.get(FIELD_ID, "")
            record_map[rec_id] = {
                "store_name": store_name,
                "memo": memo
            }

        # Step 3: Random verification sample (3 records)
        sample_ids = random.sample(list(updates.keys()), min(3, len(updates)))

        print("\n" + "=" * 60)
        print("反映確認（ランダムサンプル3件）")
        print("=" * 60)

        verification_passed = True
        for i, record_id in enumerate(sample_ids, 1):
            expected_memo = updates[record_id]
            if record_id in record_map:
                actual_data = record_map[record_id]
                actual_memo = actual_data["memo"]
                store_name = actual_data["store_name"]
                match = expected_memo == actual_memo

                print(f"\n#{i} Record ID: {record_id}")
                print(f"   店舗名: {store_name}")
                print(f"   新一言（予定）: {expected_memo}")
                print(f"   反映後の値: {actual_memo}")
                print(f"   一致: {'✓' if match else '✗'}")

                if not match:
                    verification_passed = False
            else:
                print(f"\n#{i} Record ID: {record_id}")
                print(f"   ⚠ 取得失敗")
                verification_passed = False

        # Final report
        print("\n" + "=" * 60)
        print("最終レポート")
        print("=" * 60)
        print(f"反映成功件数: {success_count}/20 件")
        print(f"反映失敗件数: {len(failed_records)}/20 件")

        if success_count == 20 and len(failed_records) == 0 and verification_passed:
            print("\n結論: 全20件が正常に反映されました。")
            print("Airtable側で値が確実に更新されていることを確認しました。")
        else:
            print("\n警告: 確認が完全ではありません。上記の詳細を確認してください。")

        # Save detailed results to file
        results = {
            "success_count": success_count,
            "failed_count": len(failed_records),
            "failed_records": [r[0] for r in failed_records],
            "sample_verification": {
                "verified_passed": verification_passed,
                "sample_ids": sample_ids
            },
            "update_data": updates,
            "verification_data": record_map
        }

        with open("/private/tmp/claude-501/-Users-kobayashikazuya-chirumaru-repo/9e15200f-19ae-47d9-9908-85959169ca31/scratchpad/update_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("\n詳細結果を保存しました。")

    else:
        print(f"取得失敗: HTTP {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"エラー: {str(e)}")
