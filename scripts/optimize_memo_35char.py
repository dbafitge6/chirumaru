#!/usr/bin/env python3
"""
Airtable 全387店舗の「一言メモ」を35字以内で書き直すスクリプト
Instagram 動画テロップ用（3秒で読める長さ）

実装仕様：
- 既存フィールド（シーンタグ、メニュー、営業時間、説明）を優先使用
- 35字以内で書き直し（既存情報に新しい視点を加える）
- 新情報の追加は出典を記録
- ログファイル（logs/memo_35char_YYYYMMDD.md）に結果出力
"""

import os
import sys
from pathlib import Path
import requests
from datetime import datetime
import json


# ==================== ヘルパー関数定義 ====================

def shorten_memo(memo, max_length):
    """
    メモを最大文字数に短縮
    句点「。」で切る、または単語境界で切る
    """
    if len(memo) <= max_length:
        return memo

    # 句点「。」で切ることを優先
    truncated = memo[:max_length]
    last_period = truncated.rfind("。")
    if last_period > 0:
        return memo[:last_period + 1]

    # 「、」で切ることを試す
    last_comma = truncated.rfind("、")
    if last_comma > max_length * 0.6:  # 60%以上の長さがあれば採用
        return memo[:last_comma]

    # 上記ダメなら max_length 字で切る
    return memo[:max_length]


def extract_primary_menu(menus):
    """
    メニュー情報から主要商品名を抽出
    複数品目がある場合は最初の1〜2個を選ぶ
    """
    if not menus:
        return ""

    # 最初の改行or句読点までを取得
    menu_list = menus.split("\n")[0].split("、")
    primary = menu_list[0].strip() if menu_list else ""

    if not primary:
        return ""

    # 長すぎる場合は調整
    if len(primary) > 25:
        primary = shorten_memo(primary, 25)

    return primary


def extract_first_sentence(text, max_length):
    """
    テキストから最初の1文を抽出
    """
    if not text:
        return ""

    # 句点「。」で分割
    sentences = text.split("。")
    if sentences:
        first = sentences[0].strip()
        if len(first) > max_length:
            first = first[:max_length]
        return first

    return ""


def extract_tag_features(tags):
    """
    シーンタグから営業特性を抽出
    複数タグがある場合は最初の1〜2個を選ぶ
    """
    if not tags:
        return ""

    features = []

    # 営業時間関連タグ
    if "夜まで営業" in tags:
        features.append("夜営業")
    elif "日曜営業" in tags:
        features.append("日曜営業")

    # その他タグ
    if "ランチあり" in tags and "夜営業" not in features:
        features.append("ランチ対応")
    if "駐車場" in tags and len(features) < 2:
        features.append("駐車場有")

    if not features:
        return ""

    return "、".join(features[:2])


def generate_from_fields_smart(menus, tags, description, business_hours):
    """
    メニュー・説明・タグから35字以内の一言メモを生成

    優先順位：
    1. メニュー情報から主要商品を抽出
    2. 説明文を補足
    3. 営業時間やタグから特徴を追加
    """

    parts = []

    # ステップ1: メニュー情報から主要商品を抽出
    menu_main = extract_primary_menu(menus)
    if menu_main:
        parts.append(menu_main)

    # ステップ2: 説明文から補足を抽出（最初の1文）
    if description and not parts:
        desc_first = extract_first_sentence(description, max_length=20)
        if desc_first:
            parts.append(desc_first)

    # ステップ3: 営業特性タグを追加
    tag_features = extract_tag_features(tags)
    if tag_features:
        parts.append(tag_features)

    # 組み合わせ
    if not parts:
        return ""

    memo = "。".join(parts) if len(parts) > 1 else parts[0]

    # 35字に調整
    if len(memo) > 35:
        memo = shorten_memo(memo, 35)

    return memo


def generate_optimized_memo(shop_name, old_memo, tags, menus, business_hours, description, area):
    """
    既存フィールドから35字以内の新しい一言メモを生成

    ルール：
    1. 既存一言が35字以内で、品質が高い場合は保留
    2. 既存一言が長い場合は短縮
    3. 既存一言がない場合は、メニュー+説明+タグから生成

    返り値: (new_memo, source)
    """

    # ケース1: 既存一言メモが既に35字以内
    if old_memo and len(old_memo) <= 35:
        return old_memo, "既存一言（35字以内）"

    # ケース2: 既存一言メモが長い場合は短縮
    if old_memo and len(old_memo) > 35:
        shortened = shorten_memo(old_memo, 35)
        return shortened, f"既存一言の短縮"

    # ケース3: 既存一言メモがない場合は、フィールドから生成
    generated = generate_from_fields_smart(
        menus=menus,
        tags=tags,
        description=description,
        business_hours=business_hours
    )

    if generated:
        return generated, "フィールド組み合わせ"

    # ケース4: どうしても生成できない場合は空にする
    return "", "情報不足"


# ==================== メイン処理 ====================

# .env ファイルを読み込む
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
if not AIRTABLE_TOKEN:
    print("ERROR: AIRTABLE_TOKEN が .env から取得できません")
    sys.exit(1)

BASE_ID = "appyyoKM7RprQRht8"
TABLE_ID = "tblcOdcqCxzb7kX0e"

headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

# ==================== フェーズ1: 全レコード取得 ====================
print("\n📥 Airtable からデータを取得中...")
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
all_records = []
offset = None

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

print(f"✓ 全レコード取得完了: {len(all_records)}件")

# ==================== フェーズ2: 各店舗を処理 ====================
print("\n🔍 各店舗の「一言メモ」を分析中...")

results = []
count_modified = 0
count_preserved = 0

for i, record in enumerate(all_records, 1):
    fields = record.get("fields", {})

    shop_name = fields.get("Store Name", "(店名不明)")
    old_memo = fields.get("一言", "") or ""
    tags = fields.get("シーン", []) or []
    menus = fields.get("メニュー", "") or ""
    business_hours = fields.get("Business Hours", "") or ""
    description = fields.get("一言メモ", "") or ""  # 詳細な説明フィールド
    area = fields.get("Area", "") or ""

    # 新しい一言メモを生成（既存情報から35字以内）
    new_memo, source = generate_optimized_memo(
        shop_name=shop_name,
        old_memo=old_memo,
        tags=tags,
        menus=menus,
        business_hours=business_hours,
        description=description,
        area=area
    )

    # 修正状況の判定
    if new_memo != old_memo:
        count_modified += 1
        status = "修正"
    else:
        count_preserved += 1
        status = "保留"

    results.append({
        "id": record.get("id"),
        "shop_name": shop_name,
        "old_memo": old_memo,
        "new_memo": new_memo,
        "char_count": len(new_memo),
        "source": source,
        "status": status,
    })

    if i % 50 == 0:
        print(f"  進捗: {i}/{len(all_records)}件")

print(f"✓ 分析完了")
print(f"  修正予定: {count_modified}件")
print(f"  保留（既存整理）: {count_preserved}件")

# ==================== フェーズ3: ログファイル生成 ====================
today = datetime.now().strftime("%Y%m%d")
log_file = Path(__file__).parent.parent / "logs" / f"memo_35char_{today}.md"

print(f"\n📝 ログファイルを生成中: {log_file}")

log_content = f"""# 一言メモ35字化レポート

処理日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
処理対象: {len(all_records)} 店舗

## 処理結果サマリー

- **修正予定**: {count_modified}件
- **保留（既存整理）**: {count_preserved}件
- **35字超過**: {sum(1 for r in results if r['char_count'] > 35)}件

## 修正内容一覧

| # | 店舗名 | 旧一言 | 新一言 | 文字数 | 出典/説明 |
|---|--------|--------|--------|--------|-----------|
"""

for i, result in enumerate(results, 1):
    # Markdown テーブルエスケープ
    shop_name = result["shop_name"].replace("|", "\\|")
    old_memo = result["old_memo"].replace("|", "\\|") if result["old_memo"] else "（なし）"
    new_memo = result["new_memo"].replace("|", "\\|")
    source = result["source"].replace("|", "\\|")

    log_content += f"| {i} | {shop_name} | {old_memo} | {new_memo} | {result['char_count']} | {source} |\n"

# ログファイルを保存
log_file.parent.mkdir(parents=True, exist_ok=True)
with open(log_file, "w", encoding="utf-8") as f:
    f.write(log_content)

print(f"✓ ログファイル保存完了: {log_file}")

# ==================== フェーズ4: 完了報告 ====================
print(f"\n{'='*60}")
print(f"✓ 処理完了：{count_modified}件修正予定、{count_preserved}件既存整理")
print(f"{'='*60}")
print(f"\n📊 ログファイル: {log_file}")
print(f"\nAirtableへの反映はしていません（ユーザー確認待ち）")
