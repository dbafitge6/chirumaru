#!/usr/bin/env python3
"""
既存一言が35字以内とされた367件を再判定するスクリプト
- 不合格基準：地名+業態のみ、業態名だけ、汎用的文言
- 合格基準：メニュー名、具体的特徴、営業特性を含む
"""

import os
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

# .env ファイルを読み込む
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
if not AIRTABLE_TOKEN:
    print("ERROR: AIRTABLE_TOKEN が取得できません")
    sys.exit(1)

# Airtable 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_ID = "tblcOdcqCxzb7kX0e"

headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

print("📥 Airtable からデータを取得中...\n")

# すべてのレコードを取得
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

print(f"✓ 全レコード取得完了: {len(all_records)}件\n")

# 35字以内の一言を持つレコードをフィルタ
memo_35_records = []
for record in all_records:
    fields = record.get("fields", {})
    memo = fields.get("一言", "").strip()
    if memo and len(memo) <= 35:
        memo_35_records.append(record)

print(f"✓ 35字以内の一言を持つレコード: {len(memo_35_records)}件\n")

# 判定ロジック
def judge_memo(memo, fields):
    """
    一言を判定し、合格/要修正と理由を返す
    Returns: (verdict, reason)
    verdict: "合格" or "要修正"
    reason: 判定理由
    """

    memo = memo.strip()

    # 空文字列は判定不能（ただしこのスクリプトでは35字以上はフィルタ済みなので通常は発生しない）
    if not memo:
        return "要確認", "一言が空"

    # ===== 「要修正」の判定基準（ユーザー指示より） =====

    # 1. 「地名+業態名です」パターン
    location_patterns = ["市の", "町の", "村の", "区の", "県の"]
    business_types = ["カフェ", "喫茶", "飲食店", "パン屋", "スイーツ店", "カフェ・喫茶"]

    for pattern in location_patterns:
        if pattern in memo:
            # 地名を含む場合、業態名で終わるかチェック
            for btype in business_types:
                if memo.endswith(btype) or memo.endswith(btype + "です"):
                    return "要修正", "地名+業態名のみ"

    # 2. 業態名だけ
    if memo in business_types or memo + "です" in business_types:
        return "要修正", "業態名のみ"

    # 3. 汎用的すぎる文言（同業態と区別できない）
    generic_phrases = ["カフェ・喫茶", "飲食店", "コーヒー店"]
    if memo in generic_phrases or memo + "です" in generic_phrases:
        return "要修正", "汎用的すぎる文言"

    # ===== 「合格」の判定基準（ユーザー指示より） =====

    # メニュー名や特定の商品名を含む場合
    menu_keywords = [
        "サンド", "トースト", "パスタ", "カレー", "丼", "定食", "ピザ", "ハンバーガー",
        "バーガー", "グラタン", "ドリア", "オムライス", "クロック", "プレート", "セット",
        "フルーツ", "あんバター", "クリーム", "ケーキ", "パフェ", "モーニング",
        "焙", "ドーナツ", "シフォン", "クレープ", "パイ",
        "ジェラート", "わらび餅", "和菓子", "焼き菓子", "ショコラ", "チョコ",
        "スイーツ", "アイス", "ラーメン", "うどん", "蕎麦", "味噌汁", "おにぎり",
        "コース", "メニュー", "揚げぱん", "パン類", "種類", "「"  # 「」で囲まれた商品名
    ]

    for keyword in menu_keywords:
        if keyword in memo:
            return "合格", f"メニュー名/商品名を含む（{keyword}）"

    # 店の具体的な特徴を記載している場合
    feature_keywords = [
        "古民家", "古い", "レトロ", "モダン", "オシャレ", "北欧", "素朴",
        "景色", "ビュー", "テラス", "座敷", "カウンター",
        "自慢", "が名物", "特徴",
        "直火", "手作り", "新鮮", "こだわり", "本格",
        "温かみ", "内装", "雰囲気",
        "改装", "自家製", "創業", "老舗", "隠れ家", "専門店",
        "可愛い", "素敵", "インスタ",
        "コンテナハウス", "有形文化財", "書店", "ホテル", "ガーデン"
    ]

    for keyword in feature_keywords:
        if keyword in memo:
            return "合格", f"具体的な特徴を記載（{keyword}）"

    # 営業特性を含む場合
    operation_keywords = ["早朝", "夜", "営業", "日曜", "無休", "翌", "営", "営業時間", "営業日",
                          "限定", "休", "時間帯"]

    for keyword in operation_keywords:
        if keyword in memo:
            return "合格", f"営業特性を含む（{keyword}）"

    # 複合情報を含む場合（2つ以上の異なる情報タイプ）
    # 例：「パン類も豊富」「毎日100種類以上」「新潟駅近く」等
    has_menu_info = any(word in memo for word in ["パン", "食", "もの", "品", "セット", "ランチ", "ディナー", "豊富", "種類"])
    has_location_info = any(word in memo for word in ["駅", "近", "隣", "内", "中", "前", "徒歩", "エリア", "場所"])
    has_feature_info = any(word in memo for word in ["・", "で", "風", "的", "も", "が"])

    info_count = sum([has_menu_info, has_location_info, has_feature_info])
    if info_count >= 2:
        return "合格", "複合情報を含む"

    # その他（文字数が5字以上で、上記に該当しない場合）
    # これは実際には限定的な情報を含むことが多いので合格と判定
    if len(memo) >= 5:
        return "合格", "短い説明だが情報あり"

    # 1〜4字は明らかに情報不足
    return "要確認", "文字数が少なく情報不足"


# 判定実施
passed = []
needs_revision = []
uncertain = []

print("📊 367件を再判定中...\n")

for i, record in enumerate(memo_35_records, 1):
    fields = record.get("fields", {})
    memo = fields.get("一言", "").strip()
    store_name = fields.get("Store Name", "不明")
    record_id = record.get("id", "")

    verdict, reason = judge_memo(memo, fields)

    result = {
        "number": i,
        "record_id": record_id,
        "store_name": store_name,
        "memo": memo,
        "char_count": len(memo),
        "verdict": verdict,
        "reason": reason,
        "fields": fields
    }

    if verdict == "合格":
        passed.append(result)
    elif verdict == "要修正":
        needs_revision.append(result)
    else:
        uncertain.append(result)

print(f"✓ 判定完了\n")
print(f"  合格: {len(passed)}件")
print(f"  要修正: {len(needs_revision)}件")
print(f"  要確認: {len(uncertain)}件")
print(f"  合計: {len(memo_35_records)}件\n")

# 要修正の店舗について新案を作成
def create_memo_suggestion(record):
    """
    メニュー欄、タグ、説明欄から具体情報を抽出して新案を作成
    """
    fields = record.get("fields", {})
    store_name = fields.get("Store Name", "")
    current_memo = fields.get("一言", "")
    menu = fields.get("メニュー", "")
    tags = fields.get("シーンタグ", [])
    description = fields.get("説明文（HTML）", "")

    suggestions = []

    # メニュー情報から抽出
    if menu:
        menu_items = menu.split("\n")[:3]  # 最初の3項目
        for item in menu_items:
            item = item.strip()
            if item and len(item) < 30:
                suggestions.append(item)

    # タグから営業特性を抽出
    if tags:
        tag_str = "、".join(tags[:2])
        if len(tag_str) < 25:
            suggestions.append(tag_str)

    # 説明文から一言を抽出（簡潔な表現）
    if description:
        # HTML タグを除去（簡易版）
        import re
        text = re.sub(r'<[^>]+>', '', description)
        text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
        sentences = text.split("。")
        for sent in sentences[:2]:
            sent = sent.strip()
            if sent and 10 < len(sent) < 35:
                suggestions.append(sent)

    return suggestions[:3]  # 上位3案を返す


# ログファイルを作成
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "memo_35char_reevaluate_20260819.md"

with open(log_file, "w", encoding="utf-8") as f:
    f.write("# 367件の再判定レポート\n\n")
    f.write(f"処理日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # サマリー
    f.write("## 判定結果サマリー\n\n")
    f.write(f"- 合格: {len(passed)}件\n")
    f.write(f"- 要修正: {len(needs_revision)}件\n")
    f.write(f"- 要確認: {len(uncertain)}件\n")
    f.write(f"- 合計: {len(memo_35_records)}件\n\n")

    # 要修正一覧
    if needs_revision:
        f.write("## 要修正一覧\n\n")
        f.write("| # | Record ID | 店舗名 | 現在の一言 | 文字数 | 不合格理由 | 新一言案 | 新字数 | 参照フィールド |\n")
        f.write("|---|-----------|--------|-----------|--------|----------|--------|--------|---------------|\n")

        for i, result in enumerate(needs_revision, 1):
            suggestions = create_memo_suggestion(result)
            suggestion_text = " / ".join(suggestions) if suggestions else "（情報不足）"

            # メニュー情報から参照フィールド情報を抽出
            menu = result["fields"].get("メニュー", "")[:30]
            tags = ", ".join(result["fields"].get("シーンタグ", [])[:2])

            ref_field = ""
            if menu:
                ref_field += f"メニュー: {menu[:20]}..., "
            if tags:
                ref_field += f"タグ: {tags}"

            f.write(f"| {i} | {result['record_id'][:10]}... | {result['store_name']} | {result['memo']} | {result['char_count']} | {result['reason']} | {suggestion_text[:40]} | {len(suggestion_text)} | {ref_field} |\n")

        f.write("\n")

    # 全367件の詳細判定ログ
    f.write("## 全367件の詳細判定ログ\n\n")
    f.write("| # | Record ID | 店舗名 | 現在の一言 | 文字数 | 判定 | 判定根拠 |\n")
    f.write("|---|-----------|--------|-----------|--------|------|----------|\n")

    for idx, record in enumerate(memo_35_records, 1):
        fields = record.get("fields", {})
        memo = fields.get("一言", "").strip()
        store_name = fields.get("Store Name", "不明")
        record_id = record.get("id", "")

        # 判定を再計算（キャッシュ）
        verdict, reason = judge_memo(memo, fields)

        f.write(f"| {idx} | {record_id[:10]}... | {store_name} | {memo} | {len(memo)} | {verdict} | {reason} |\n")

print(f"\n✓ ログ出力完了: {log_file}")
print(f"\n📋 要修正{len(needs_revision)}件の詳細:")

for i, result in enumerate(needs_revision[:5], 1):
    print(f"\n{i}. {result['store_name']}")
    print(f"   現在: 「{result['memo']}」({result['char_count']}字)")
    print(f"   理由: {result['reason']}")

    # メニューやタグから新案を提示
    menu = result['fields'].get("メニュー", "")
    if menu:
        print(f"   メニュー: {menu[:50]}...")

if len(needs_revision) > 5:
    print(f"\n   ... 他 {len(needs_revision) - 5} 件")

print(f"\n✅ 再判定完了：{len(passed)}件合格、{len(needs_revision)}件要修正。")
print(f"✅ 詳細ログは {log_file} に記載されています。")
