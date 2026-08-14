#!/usr/bin/env python3
"""
384件の説明文から定型文を除去し、20文字以内の一言を生成する
改善版：
- 20文字超の場合は切らない。別の候補を探すか空にする
- 候補の優先順位：立地・名物・特徴 > 開業年・営業時間
- 括弧が開いたまま終わる場合は括弧の手前で切る
"""

import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

# .env ファイルを読み込む
env_file = Path(".env")
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

# 定型文41種
BOILERPLATE_TEXTS = [
    "ドライブや散策の際のご立ち寄りにもおすすめです。",
    "朝からの営業で、朝食やモーニングセットをお楽しみいただけます。",
    "新潟県内でおすすめのスポットとしてご紹介させていただきます。",
    "くつろぎながらお時間をお過ごしいただける空間となっています。",
    "訪問の際は、営業時間や詳細情報をご確認いただくことをおすすめします。",
    "全国チェーン。",
    "訪問前にお電話またはウェブサイトでご確認ください。",
    "こだわりの素材を使用した、質の高い商品をご提供しています。",
    "毎日新鮮な商品を豊富に取り揃えています。",
    "季節限定商品もございます。",
    "焼き立てのパンをお気軽にお選びいただけます。",
    "ケーキなどのスイーツが充実しています。",
    "訪問の際はお電話でご確認いただくことをおすすめします。",
    "お一人での利用から団体様まで対応しています。",
    "営業時間：07:00-23:00 年中無休。",
    "コーヒーも取り扱っています。",
    "営業時間や詳細情報については、公式ウェブサイトやSNSでご確認いただくか、お電話でお問い合わせください。",
    "営業時間：月〜金 9:00-21:00 土日 8:00-21:00(L.O.閉店30分前) 定休なし。",
    "長岡市のカフェ・飲食店です。",
    "新潟市中央区のカフェ・飲食店です。",
    "営業時間：月〜金 9:00-22:00 土日 8:00-22:00(L.O.閉店30分前) 定休なし。",
    "2026年5月オープン。",
    "2022年5月オープン。",
    "新発田市のカフェ・飲食店です。",
    "浅煎りコーヒーと『コブ』が特徴的なふわもちドーナツが絶品。",
    "営業時間：7:00-22:00 年中無休。",
    "2026年4月オープン。",
    "2025年1月オープン。",
    "2024年6月オープン。",
    "駐車場10台。",
    "2023年3月オープン。",
    "自家製ソースとふわふわ氷。",
    "ペンギンマークが目印。",
    "営業時間：10:00〜16:00 水曜定休。",
    "営業時間：9:00~18:00 定休なし。",
    "2024年10月オープン。",
    "2023年11月OPEN。",
    "営業時間：07:00-22:00 年中無休。",
    "ITOYA関連企業が運営。",
    "イートインスペースあり。",
    "営業時間：10:00-19:00。",
]

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# 全レコード取得（curl使用）
print("🔄 全レコードを取得中...")
all_records = []
offset = None

while True:
    full_url = f"{url}?returnFieldsByFieldId=true"
    if offset:
        full_url += f"&offset={offset}"

    result = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Bearer {AIRTABLE_TOKEN}", full_url],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ curl エラー: {result.returncode}")
        exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ JSON パースエラー: {result.stdout[:200]}")
        exit(1)

    if 'error' in data:
        print(f"❌ API エラー: {data['error']}")
        exit(1)

    all_records.extend(data.get('records', []))
    offset = data.get('offset')
    if not offset:
        break

print(f"✅ 取得完了: {len(all_records)} 件\n")

# データ構造化
shops = []
for record in all_records:
    fields = record.get('fields', {})
    shops.append({
        'id': record['id'],
        'name': fields.get('fldpEdbx8RE5XfBln', ''),
        'description': fields.get('fld7kYvLqO0lLFEWU', ''),
    })

REGIONS = {
    '新潟県', '新潟市', '長岡市', '三条市', '柏崎市', '新発田市', '小千谷市',
    '加茂市', '十日町市', '見附市', '村上市', '燕市', '糸魚川市', '妙高市',
    '五泉市', '上越市', '阿賀野市', '湯沢町', '津南町', '中央区', '東区',
    '北区', '秋葉区', '南区', '西区', '西蒲区', '弥彦村', '関川村'
}

def has_region_keyword(text):
    """テキストに地域キーワードが含まれているかチェック"""
    for region in REGIONS:
        if region in text:
            return True
    return False

def is_template_sentence(sentence, shop_name):
    """「〜は△△市の××です」型テンプレート文かチェック"""
    if not sentence.endswith("です"):
        return False
    name_chars = shop_name[:min(3, len(shop_name))]
    if name_chars in sentence and has_region_keyword(sentence):
        return True
    return False

def remove_boilerplate(text, shop_name):
    """説明文から定型文と初期テンプレートを除去"""
    if not text:
        return ""

    result = text
    for boilerplate in BOILERPLATE_TEXTS:
        result = result.replace(boilerplate, " ")
        result = result.replace(boilerplate.rstrip("。"), " ")

    # 文に分割
    sentences = result.split("。")
    filtered_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if is_template_sentence(sentence, shop_name):
            continue
        if "メニューとして" in sentence and "提供されています" in sentence:
            continue
        if sentence.startswith("訪問の際"):
            continue

        filtered_sentences.append(sentence)

    result = "。".join(filtered_sentences)
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def close_unclosed_brackets(text):
    """開いたままの括弧を処理する（緩和版）
    複数の開いた括弧を繰り返し処理
    """
    if not text:
        return text

    bracket_pairs = {
        '「': '」',
        '『': '』',
        '（': '）',
        '(': ')',
    }

    # 開かれたままの括弧がなくなるまで繰り返し処理
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # 開かれたままの括弧を探す
        has_unclosed = False
        last_open_pos = -1
        last_open_bracket = None

        for open_bracket, close_bracket in bracket_pairs.items():
            open_count = text.count(open_bracket)
            close_count = text.count(close_bracket)

            if open_count > close_count:
                has_unclosed = True
                pos = text.rfind(open_bracket)
                if pos >= 0 and pos > last_open_pos:
                    last_open_pos = pos
                    last_open_bracket = open_bracket

        # 開かれたままの括弧がない場合
        if not has_unclosed:
            return text

        if last_open_pos < 0:
            return text

        # 括弧の手前
        before_bracket = text[:last_open_pos].rstrip()
        bracket_content = text[last_open_pos + 1:].strip()

        # 括弧内が短い場合、括弧を閉じる試み
        if len(bracket_content) <= 6 and last_open_bracket in bracket_pairs:
            close_bracket = bracket_pairs[last_open_bracket]
            text = before_bracket + " " + last_open_bracket + bracket_content + close_bracket
            continue

        # 括弧の手前で切れるか判定
        if len(before_bracket) < 5:
            # 短すぎる場合は採用不可
            return None

        # 読点で終わっているか、意味のある情報を含んでいるか
        ends_with_read = before_bracket.endswith('、')
        has_meaningful = any(
            keyword in before_bracket
            for keyword in ['カフェ', 'パン', '店', '焙煎', '自家製', 'コーヒー', 'スイーツ', '菓子', '専門店']
        )

        if ends_with_read or has_meaningful:
            # この括弧の手前まで採用
            text = before_bracket
            # 次のループで次の開いた括弧を処理
        else:
            # 意味が通らないので採用しない
            return None

    return text

def is_excluded_content(sentence):
    """除外すべき内容かチェック
    - 営業時間のみ
    - 開業年のみ
    - 地域＋業種のみ
    """
    if not sentence:
        return True

    # 営業時間のみ
    if re.match(r'^営業時間', sentence):
        return True

    # 開業年のみ（「2023年11月オープン」等）
    if re.match(r'^(20\d{2}年|令和|平成)', sentence) and 'オープン' in sentence:
        return True

    # 地域＋業種のみ（「新潟市中央区のカフェです」等）
    if has_region_keyword(sentence) and any(
        cat in sentence for cat in ['カフェ', 'パン', 'ケーキ', '喫茶', 'バー', 'レストラン', 'ジェラート', 'スイーツ']
    ) and sentence.endswith(('です', 'です。')):
        # ただし、より詳しい情報がある場合は除外しない
        # 例：「新潟市中央区の老舗カフェです」は除外
        # 「新潟市中央区のカフェです」は除外
        if len(sentence) < 20:  # 簡潔すぎる場合は除外候補
            return True

    return False

def categorize_candidate(sentence):
    """候補文をカテゴリ分けして優先順位を決定
    戻り値: (優先順位, 具体性スコア, センテンス)
    優先順位: 1=特徴・雰囲気・立地, 2=名物・メニュー, 3=沿革・歴史, 4=営業条件, 5=その他
    """

    # 特徴・雰囲気・立地情報
    if any(keyword in sentence for keyword in [
        '駅', '敷地内', '街', 'ホテル', '古民家', '建物', 'コンテナ',
        '改装', 'リノベーション', 'オシャレ', '落ち着いた', '有形文化財',
        '雰囲気', 'テラス', '景観', '庭', 'ガーデン', '川沿い', '立地',
        '住宅街', '隠れ家', 'アットホーム'
    ]):
        specificity = len([k for k in [
            '駅', '敷地内', 'ホテル', '古民家', 'コンテナ', '改装', 'リノベーション', 'テラス', 'ガーデン'
        ] if k in sentence]) * 10
        return (1, specificity, sentence)

    # 名物・看板メニューの説明
    if any(keyword in sentence for keyword in [
        '名物', 'が人気', '専門', 'メニュー', 'こだわり', 'パン', 'ケーキ', 'スイーツ',
        'コーヒー', 'サンド', 'スープ', '丼', 'パスタ', 'ピザ', 'ジェラート',
        'シカのマーク', 'ペンギン', 'マーク', 'ロゴ'
    ]):
        specificity = len([k for k in [
            'が人気', '専門', 'パン', 'ケーキ', 'スイーツ', 'コーヒー', 'シカ', 'ペンギン'
        ] if k in sentence]) * 10
        return (2, specificity, sentence)

    # 沿革・歴史
    if re.search(r'(20\d{2}年|令和|平成|創業|年創業|周年)', sentence):
        specificity = 5  # 履歴情報は具体性が低い
        return (3, specificity, sentence)

    # 営業条件（営業日、営業時間、予約制など）
    if any(keyword in sentence for keyword in [
        '営業', 'のみ営業', '定休', '予約', '時間', '曜日'
    ]):
        specificity = 0
        return (4, specificity, sentence)

    # その他
    return (5, 0, sentence)

def extract_tagline(cleaned_text):
    """20文字以内の一言を抽出
    【改善版】
    - 候補を優先順位でカテゴリ分け
    - 同じカテゴリなら具体性スコアで選択
    - 括弧の処理を緩和
    """
    if not cleaned_text:
        return ""

    sentences = cleaned_text.split("。")
    candidates = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # 除外内容かチェック
        if is_excluded_content(sentence):
            continue

        # 20文字以内かチェック
        if len(sentence) > 20:
            # 括弧を処理してから再度チェック
            processed = close_unclosed_brackets(sentence)
            if processed is None:
                # 括弧処理で採用不可と判定
                continue
            if len(processed) > 20:
                # 20文字を超えるので候補から除外
                continue
            sentence = processed
        else:
            # 20文字以内でも括弧を処理
            processed = close_unclosed_brackets(sentence)
            if processed is None:
                continue
            sentence = processed

        # 候補に追加（カテゴリ化）
        category, specificity, _ = categorize_candidate(sentence)
        candidates.append((category, specificity, sentence))

    # 候補がない場合は空
    if not candidates:
        return ""

    # 優先順位でソート（カテゴリ昇順、同じカテゴリなら具体性降順）
    candidates.sort(key=lambda x: (x[0], -x[1]))

    return candidates[0][2]

# 全384件を20件ずつ処理
print("=" * 80)
print("【全384件を処理中】")
print("=" * 80)

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "tagline_gen.md"

# ログファイルを初期化
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"# 一言生成ログ（全384件）\n\n")
    f.write(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

# 統計情報収集用
all_results = []
empty_records = []

# 20件ずつ処理
batch_size = 20
total_batches = (len(shops) + batch_size - 1) // batch_size

for batch_num in range(total_batches):
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, len(shops))
    batch_shops = shops[start_idx:end_idx]

    batch_results = []
    batch_empty_count = 0

    print(f"\n【バッチ {batch_num + 1}/{total_batches}】 {start_idx + 1}件目～{end_idx}件目を処理中...")

    for i, shop in enumerate(batch_shops):
        idx = start_idx + i
        cleaned = remove_boilerplate(shop['description'], shop['name'])
        tagline = extract_tagline(cleaned)

        if not tagline:
            batch_empty_count += 1
            empty_records.append((idx + 1, shop['name']))

        preview = cleaned[:40] if cleaned else "(除去後に情報なし)"

        result = {
            'idx': idx + 1,
            'name': shop['name'],
            'preview': preview,
            'tagline': tagline,
            'char_count': len(tagline),
            'is_empty': not tagline,
        }
        batch_results.append(result)
        all_results.append(result)

        status = "✓" if tagline else "✗"
        print(f"  {idx + 1:3d}. {shop['name']:<40} {status}", end="")
        if tagline:
            print(f" → {tagline[:20]}")
        else:
            print()

    # ログファイルに追記
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"## バッチ {batch_num + 1} ({start_idx + 1}～{end_idx}件)\n\n")
        f.write(f"空になった件数: {batch_empty_count}/{len(batch_results)}\n\n")
        f.write(f"| # | 店名 | 除去後の説明文（40字まで） | 生成した一言 | 文字数 | 状態 |\n")
        f.write(f"|---|------|---------------------------|---------|------|---------|\n")

        for result in batch_results:
            status = "空" if result['is_empty'] else "採用"
            f.write(f"| {result['idx']:03d} | {result['name']} | {result['preview']} | {result['tagline'] or '(空)'} | {result['char_count']} | {status} |\n")

        f.write("\n")

    print(f"  バッチ完了：空 {batch_empty_count}/{len(batch_results)} ({batch_empty_count*100//len(batch_results)}%)")

# 統計情報計算
total_count = len(all_results)
total_empty = sum(1 for r in all_results if r['is_empty'])
total_adopted = total_count - total_empty

char_counts = [r['char_count'] for r in all_results if not r['is_empty']]
min_char = min(char_counts) if char_counts else 0
max_char = max(char_counts) if char_counts else 0
avg_char = sum(char_counts) / len(char_counts) if char_counts else 0

# 最終レポートをログに追加
with open(log_file, 'a', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("## 最終レポート\n\n")
    f.write(f"実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**全体統計**\n")
    f.write(f"- 総件数: {total_count}件\n")
    f.write(f"- 採用: {total_adopted}件 ({total_adopted*100//total_count}%)\n")
    f.write(f"- 空: {total_empty}件 ({total_empty*100//total_count}%)\n\n")
    f.write(f"**一言の文字数分布**\n")
    f.write(f"- 最短: {min_char}文字\n")
    f.write(f"- 最長: {max_char}文字\n")
    f.write(f"- 平均: {avg_char:.1f}文字\n\n")
    f.write(f"**空になったレコード({total_empty}件)**\n\n")
    if empty_records:
        for idx, name in empty_records:
            f.write(f"- {idx:03d}. {name}\n")
    else:
        f.write("(なし)\n")

# コンソール出力
print("\n" + "=" * 80)
print("✅ 全384件の処理完了")
print("=" * 80)
print(f"\n📊 最終統計")
print(f"  総件数: {total_count}件")
print(f"  採用: {total_adopted}件 ({total_adopted*100//total_count}%)")
print(f"  空: {total_empty}件 ({total_empty*100//total_count}%)")
print(f"\n📝 一言の文字数分布")
print(f"  最短: {min_char}文字")
print(f"  最長: {max_char}文字")
print(f"  平均: {avg_char:.1f}文字")
print(f"\n📋 ログファイル: {log_file}")
print("=" * 80)
