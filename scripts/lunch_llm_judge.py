#!/usr/bin/env python3
"""
ランチあり タグ LLM 判定スクリプト
Claude Sonnet を使用してメニューテキストから食事メニューの有無を判定
"""

import os
import json
import requests
from pathlib import Path
import time

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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

MENU_FIELD = "fldy7L16dxfRmpPVa"  # メニュー
SCENE_FIELD = "fldDl6OsS4EKmJT18"  # シーン
STORE_NAME_FIELD = "fldpEdbx8RE5XfBln"  # 店名

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY が設定されていません")
    exit(1)

airtable_url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
airtable_headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

anthropic_url = "https://api.anthropic.com/v1/messages"
anthropic_headers = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

SYSTEM_PROMPT = """あなたはカフェのメニューを分類する。与えられたメニューに
「食事として成立するもの」が含まれるか判定せよ。

含まれる例: サンドイッチ(具が食事系)、パスタ、カレー、丼、定食、
ピザ、ハンバーガー、グラタン、ドリア、オムライス、クロックムッシュ、
食事系のプレート、モーニングセット

含まれない例: フルーツサンド、あんバターサンド、クリーム系サンド、
ケーキ、パフェ、スイーツプレート、ケーキセット、ドリンクのみ、
焼き菓子、パンの販売のみ

判断に迷う場合は false を返す。

出力は以下のJSONのみ。前置きや説明、コードブロックは書かない。
{"lunch": true|false, "reason": "20字以内"}"""

def judge_lunch_with_llm(menu_text, max_retries=3):
    """LLM を使用してランチメニューの有無を判定"""
    if not menu_text:
        return False, "メニューなし"

    for attempt in range(max_retries):
        try:
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": menu_text
                    }
                ],
                "system": SYSTEM_PROMPT
            }

            response = requests.post(anthropic_url, json=payload, headers=anthropic_headers, timeout=10)

            if response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt
                print(f"レート制限。{wait_time}秒待機中...")
                time.sleep(wait_time)
                continue

            if response.status_code != 200:
                print(f"⚠️  API エラー {response.status_code}: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None, f"API エラー {response.status_code}"

            data = response.json()
            content = data.get("content", [{}])[0].get("text", "").strip()

            # JSON を解析
            try:
                result = json.loads(content)
                return result.get("lunch", False), result.get("reason", "")
            except json.JSONDecodeError:
                print(f"⚠️  JSON パース失敗: {content}")
                return None, f"JSON パース失敗"

        except requests.Timeout:
            if attempt < max_retries - 1:
                print(f"タイムアウト。リトライ中... ({attempt + 1}/{max_retries})")
                time.sleep(1)
                continue
            return None, "タイムアウト"

        except Exception as e:
            print(f"⚠️  予期しないエラー: {e}")
            return None, str(e)

    return None, "リトライ上限到達"

print("=" * 80)
print("ランチあり タグ LLM 判定")
print("=" * 80)

# 全レコード取得
all_records = []
offset = None

print("\n【Step 1】全384件を取得中...")
while True:
    params = {"pageSize": 100, "returnFieldsByFieldId": "true"}
    if offset:
        params["offset"] = offset

    response = requests.get(airtable_url, headers=airtable_headers, params=params)
    if response.status_code != 200:
        print(f"❌ API エラー: {response.status_code}")
        exit(1)

    data = response.json()
    all_records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break

print(f"取得完了: {len(all_records)} 件\n")

# 現在「ランチあり」が付いているレコードを抽出
print("【Step 2】現在「ランチあり」が付いているレコードを抽出中...")

current_lunch = []
for record in all_records:
    fields = record.get('fields', {})
    tags = fields.get(SCENE_FIELD, [])
    if isinstance(tags, list) and "ランチあり" in tags:
        current_lunch.append({
            'id': record['id'],
            'name': fields.get(STORE_NAME_FIELD, 'Unknown'),
            'menu': fields.get(MENU_FIELD, '')
        })

print(f"対象レコード: {len(current_lunch)} 件\n")

# LLM 判定を実行
print("【Step 3】LLM 判定を実行中...")

results = []
false_count = 0
true_count = 0
error_count = 0

for i, rec in enumerate(current_lunch, 1):
    lunch, reason = judge_lunch_with_llm(rec['menu'])

    result = {
        'name': rec['name'],
        'menu': rec['menu'],
        'lunch': lunch,
        'reason': reason
    }
    results.append(result)

    if lunch is True:
        true_count += 1
    elif lunch is False:
        false_count += 1
    else:
        error_count += 1

    if i % 10 == 0:
        print(f"  処理中: {i}/{len(current_lunch)}")

    # レート制限対策
    time.sleep(0.5)

print(f"完了: {len(current_lunch)} 件\n")

# 結果をまとめてログ出力
log_output = []
log_output.append("=" * 80)
log_output.append("ランチあり タグ LLM 判定 結果")
log_output.append("=" * 80)
log_output.append("")
log_output.append(f"対象: 現在「ランチあり」が付いている {len(current_lunch)} 件")
log_output.append(f"判定結果: true={true_count}件, false={false_count}件, エラー={error_count}件")
log_output.append("")

# 判定が false になったレコード
false_results = [r for r in results if r['lunch'] is False]

log_output.append("=" * 80)
log_output.append(f"判定が false になったレコード（{len(false_results)}件）")
log_output.append("=" * 80)
log_output.append("")

for i, r in enumerate(false_results, 1):
    log_output.append(f"{i}. {r['name']} / {r['menu']} / {r['reason']}")

log_output.append("")

# 検証用の4件をハイライト
log_output.append("=" * 80)
log_output.append("検証用レコード（期待値との確認）")
log_output.append("=" * 80)
log_output.append("")

validation_targets = {
    '59FU': (True, 'ローストビーフと卵のサンド'),
    '暮らしの喫茶 ひとひ': (True, 'カンパーニュサンド'),
    'SEIKŌUKI': (False, 'チーズバターサンド'),
    'SWEETS SHOP 3o\'clock': (False, 'フルーツサンド')
}

for rec in results:
    for target_name, (expected, desc) in validation_targets.items():
        if target_name in rec['name']:
            actual = rec['lunch']
            status = "✓ 期待通り" if actual == expected else "✗ 不一致"
            log_output.append(f"{status}: {rec['name']}")
            log_output.append(f"  期待値: {expected}, 実際: {actual}")
            log_output.append(f"  メニュー: {rec['menu']}")
            log_output.append(f"  理由: {rec['reason']}")
            log_output.append("")

# ログを出力
log_text = "\n".join(log_output)
print(log_text)

# ファイルに保存
os.makedirs("logs", exist_ok=True)
with open("logs/lunch_llm_judge.txt", "w", encoding="utf-8") as f:
    f.write(log_text)

print("\n" + "=" * 80)
print("ログを保存しました: logs/lunch_llm_judge.txt")
print("=" * 80)
print("\n⚠️  Airtable への書き込みは実行していません")
print("上記の判定結果をご確認ください。")
