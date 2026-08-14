#!/usr/bin/env python3
"""
Airtable データ品質全件監査スクリプト
- 説明文の取り違え
- 定型文の混入
- 重複レコード（電話番号・住所）
- タグの整合性
- エリアと住所の不一致
- 必須フィールドの欠損
- シーンタグの妥当性
"""

import os
import requests
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

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

# 一般語リスト
GENERIC_WORDS = {
    'カフェ', '珈琲', 'コーヒー', 'コヒー', 'パン', 'ケーキ', 'パティスリー',
    'パン屋', 'ジェラート', 'アイス', 'スイーツ', '喫茶', '食堂', 'レストラン',
}

def normalize_phone(phone):
    if not phone or phone in ['要確認', '非公開', '見つかりません', '見つからず', '非公開SNS推奨']:
        return None
    phone = re.sub(r'[\s\-（）()−−]', '', phone)
    return phone if phone else None

def normalize_address(addr):
    if not addr:
        return ""
    addr = addr.strip()
    if '新潟県' not in addr and '新潟' in addr:
        if not addr.startswith('新潟県'):
            if addr.startswith('新潟'):
                addr = '新潟県' + addr
    addr = addr.replace('−', '-').replace('ー', '-').replace('〜', '-')
    addr = addr.replace(' ', '').replace('　', '')
    return addr

if not AIRTABLE_TOKEN:
    print("❌ AIRTABLE_TOKEN が設定されていません")
    exit(1)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# 全レコード取得
print("🔄 全レコードを取得中...")
all_records = []
offset = None

while True:
    params = {"returnFieldsByFieldId": "true"}
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

print(f"✅ 取得完了: {len(all_records)} 件\n")

# データ構造化
shops = []
for record in all_records:
    fields = record.get('fields', {})
    shops.append({
        'id': record['id'],
        'name': fields.get('fldpEdbx8RE5XfBln', ''),
        'area': fields.get('fld6sCx8y2OxZV5So', ''),
        'address': fields.get('fld4UiMRxLFmrCIfj', ''),
        'phone': fields.get('fldvO5qOtZYZaCFpm', ''),
        'description': fields.get('fld7kYvLqO0lLFEWU', ''),
        'menu': fields.get('fldy7L16dxfRmpPVa', ''),  # 正しいメニューフィールド
        'existing_tags': fields.get('fldsh2ess7aYHhJ8e', ''),
        'scene_tags': fields.get('fldDl6OsS4EKmJT18', []),
        'hours': fields.get('fld1ulQZqD0lVLpmP', ''),
    })

# ==============================
# 【1】説明文の取り違え
# ==============================
print("【1】説明文の取り違え...")
valid_names = []
for shop in shops:
    name = shop['name'].strip()
    if len(name) <= 2 or name in GENERIC_WORDS:
        continue
    valid_names.append((shop['id'], name))

mismatched_desc = []
for shop in shops:
    if not shop['description']:
        continue
    found_other_names = []
    for shop_id, shop_name in valid_names:
        if shop_id == shop['id']:
            continue
        if shop_name in shop['description']:
            found_other_names.append(shop_name)
    if found_other_names:
        mismatched_desc.append({
            'id': shop['id'],
            'name': shop['name'],
            'found_names': found_other_names,
        })

# ==============================
# 【2】定型文の混入
# ==============================
print("【2】定型文の混入...")
all_sentences = []
for shop in shops:
    if not shop['description']:
        continue
    sentences = shop['description'].split('。')
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 5:
            all_sentences.append((sent, shop['id'], shop['name']))

sentence_counter = Counter(sent for sent, _, _ in all_sentences)
duplicated_texts = {sent: count for sent, count in sentence_counter.items() if count >= 2}
duplicated_texts = dict(sorted(duplicated_texts.items(), key=lambda x: -x[1]))

# ==============================
# 【3】重複レコード
# ==============================
print("【3】重複レコード...")
phone_map = defaultdict(list)
address_map = defaultdict(list)

for shop in shops:
    phone_norm = normalize_phone(shop['phone'])
    if phone_norm:
        phone_map[phone_norm].append(shop)

    addr_norm = normalize_address(shop['address'])
    if addr_norm:
        address_map[addr_norm].append(shop)

dup_phones = {p: s for p, s in phone_map.items() if len(s) > 1}
dup_addresses = {a: s for a, s in address_map.items() if len(s) > 1}

# ==============================
# 【4】タグの整合性
# ==============================
print("【4】タグの整合性...")
tag_issues = []

for shop in shops:
    tags_str = shop['existing_tags']
    if not tags_str:
        tag_issues.append({
            'id': shop['id'],
            'name': shop['name'],
            'issue': 'タグがない',
        })
        continue

    tags = [t.strip() for t in tags_str.split('/')]

    # 空要素チェック
    if any(not t or t == '' for t in tags):
        tag_issues.append({
            'id': shop['id'],
            'name': shop['name'],
            'issue': '空のタグ要素',
        })

    # 空括弧チェック
    if any(re.search(r'\(\s*\)', t) for t in tags):
        tag_issues.append({
            'id': shop['id'],
            'name': shop['name'],
            'issue': '空括弧のタグ',
        })

    # タグ数チェック
    valid_tags = [t for t in tags if t.strip()]
    if len(valid_tags) <= 1:
        tag_issues.append({
            'id': shop['id'],
            'name': shop['name'],
            'issue': f'タグ数が {len(valid_tags)} 個',
        })

# ==============================
# 【5】エリアと住所の不一致
# ==============================
print("【5】エリアと住所の不一致...")
area_mismatch = []

for shop in shops:
    area = shop['area'].strip()
    address = shop['address'].strip()

    if not area or not address:
        continue

    # エリアの市区町村部分を抽出
    area_parts = area.split('/')
    for part in area_parts:
        part = part.strip()
        if part and part not in address:
            area_mismatch.append({
                'id': shop['id'],
                'name': shop['name'],
                'area': area,
                'address': address,
            })
            break

# ==============================
# 【6】必須フィールドの欠損
# ==============================
print("【6】必須フィールドの欠損...")
missing_fields = []

for shop in shops:
    missing = []
    if not shop['name'].strip():
        missing.append('店名')
    if not shop['address'].strip():
        missing.append('住所')
    if not shop['hours'].strip():
        missing.append('営業時間')
    if not shop['description'].strip():
        missing.append('説明文')
    if not shop['existing_tags'].strip():
        missing.append('既存タグ')

    if missing:
        missing_fields.append({
            'id': shop['id'],
            'name': shop['name'],
            'missing': ', '.join(missing),
        })

# ==============================
# 【7】シーンタグの妥当性
# ==============================
print("【7】シーンタグの妥当性...")

def extract_closed_days_advanced(hours_str):
    """定休日を抽出（改良版）"""
    if not hours_str:
        return None, "定休日記載なし"

    # 除外パターン：判定不能な記述
    if any(x in hours_str for x in ['営業時間は要確認', 'ウェブサイトで確認', '要確認']):
        return None, "判定不能（要確認）"
    if any(x in hours_str for x in ['チェックイン', 'チェックアウト']):
        return None, "判定不能（宿泊施設）"

    # 不定休
    if '不定休' in hours_str:
        return '不定休', "不定休"

    # 無休・定休なし
    if any(x in hours_str for x in ['無休', '定休なし', '休みなし', '年中無休', '定休なし']):
        return '無休', "無休"

    # パターン1：「定休」「休」等の明示的な記載
    patterns = [
        r'定休日[：:]\s*([^\n。,]*)',
        r'定休[：:]\s*([^\n。,]*)',
        r'定休\s+([^\n。,]*)',
        r'([^\n。,]*?)定休',
        r'([^\n。,]*?)休業',
    ]

    for pattern in patterns:
        match = re.search(pattern, hours_str)
        if match:
            closed_text = match.group(1).strip()
            if closed_text and len(closed_text) < 50:
                return closed_text, "明示的記載"

    # パターン2：「〇曜のみ営業」形式から定休日を推測
    if 'のみ営業' in hours_str:
        match = re.search(r'([^\n。,]*?)のみ営業', hours_str)
        if match:
            # 「木・金・土曜日のみ営業」なら日曜は営業していない
            operation_days = match.group(1).strip()
            return f"【推測】{operation_days}以外定休", "営業曜日から推測"

    # パターン3：営業時間から営業曜日を抽出
    # 例：「月～金 11:00-18:00」「火・水・木 10:00-16:00」
    # 日曜が営業曜日に含まれているか確認
    weekday_patterns = [
        r'月～金', r'月〜金', r'月-金',
        r'火～土', r'火〜土', r'火-土',
        r'月～木', r'月〜木', r'月-木',
    ]

    for pattern in weekday_patterns:
        if re.search(pattern, hours_str):
            # 日曜が明示的に記載されていないので定休と推測
            return f"【推測】{pattern}営業（日曜記載なし）", "営業曜日から推測"

    # パターン4：曜日別営業時間の複数行記述から日曜を抽出
    # 例：「月曜日: 10:00-18:00 火曜日: 10:00-18:00 ... 日曜日: 定休」
    if '日曜' in hours_str or '日曜日' in hours_str:
        sunday_match = re.search(r'日曜日?[：:]\s*([^\n]*)', hours_str)
        if sunday_match:
            sunday_info = sunday_match.group(1).strip()
            if any(x in sunday_info for x in ['定休', '休業', '休み']):
                return '日曜定休', "曜日別記述"
            elif '営業' in sunday_info or re.search(r'\d+[:：]\d+', sunday_info):
                # 日曜営業
                return '日曜営業', "曜日別記述"

    return None, "定休日の抽出に失敗"

def extract_closing_time_advanced(hours_str):
    """閉店時刻を抽出（改良版）"""
    if not hours_str:
        return None, "記載なし"

    # 除外パターン
    if any(x in hours_str for x in ['チェックイン', 'チェックアウト', '宿泊']):
        return None, "宿泊施設"
    if any(x in hours_str for x in ['営業時間は要確認', '要確認']):
        return None, "要確認"

    # 時刻パターン抽出
    time_patterns = [
        r'(\d{1,2}):(\d{2})',
        r'(\d{1,2})時(\d{2})分',
        r'(\d{1,2})[:：](\d{2})',
    ]

    times = []
    for pattern in time_patterns:
        matches = re.finditer(pattern, hours_str)
        for match in matches:
            hour = int(match.group(1))
            minute = int(match.group(2))
            times.append((hour, minute))

    if not times:
        return None, "時刻抽出失敗"

    # 最も遅い時刻を閉店時刻とする
    max_time = max(times)
    return max_time, "抽出成功"

def check_sunday_advanced(closed_days_str):
    """日曜営業判定（改良版）"""
    if closed_days_str is None:
        return False, "定休日不明"

    if closed_days_str == '無休':
        return True, None

    if closed_days_str == '不定休':
        return False, "不定休"

    # 日曜を含む定休日パターン
    if any(x in closed_days_str for x in ['日', '日曜', '日祝', '祝', '祝日']):
        return False, "日曜定休"

    # 日曜が定休に含まれていない
    if '日曜営業' in closed_days_str:
        return True, None

    # 推測パターンで日曜が営業曜日に含まれていない
    if '【推測】' in closed_days_str:
        if any(x in closed_days_str for x in ['日以外定休', '日曜記載なし', 'のみ営業']):
            return False, "推測：日曜非営業"
        return True, None

    return True, None

def check_late_night_advanced(closing_time):
    """夜営業判定（改良版）"""
    if closing_time is None:
        return False, "時刻不明"

    hour, minute = closing_time
    if hour >= 19:
        return True, None

    return False, "19時前"

no_scene_tags = []
lunch_without_food = []

for shop in shops:
    scene_tags = shop['scene_tags'] if isinstance(shop['scene_tags'], list) else []

    if not scene_tags:
        # 新しいシーンタグを判定してもいいが、ここでは「シーンタグなし」をカウント
        no_scene_tags.append({
            'id': shop['id'],
            'name': shop['name'],
        })

    # 「ランチあり」チェック（メニューフィールド fldy7L16dxfRmpPVa を確認）
    if 'ランチあり' in scene_tags:
        # 食事系キーワードを探す（メニューフィールドから）
        food_keywords = ['パスタ', 'カレー', 'ランチ', '定食', 'サンド', 'パン', 'ハンバーガー',
                        'ピザ', 'グラタン', 'ドリア', 'オムライス', 'クロック', 'プレート',
                        'ライス', 'チキン', 'ステーキ', '生姜焼き', '麻辣湯', 'ラーメン',
                        'うどん', 'そば', 'ご飯', '肉', 'スープ', '丼',
                        'バーガー', 'ガレット', 'トースト', 'クロックムッシュ', 'ワッフル']

        # メニューフィールドから食事系キーワードを検索
        menu_text = shop['menu'] if shop['menu'] else ''
        has_food = any(kw in menu_text for kw in food_keywords)

        if not has_food:
            lunch_without_food.append({
                'id': shop['id'],
                'name': shop['name'],
                'menu': menu_text[:70] if menu_text else '(メニュー記載なし)',
            })

# ==============================
# Markdown ファイルに出力
# ==============================
output_dir = Path("logs")
output_dir.mkdir(exist_ok=True)

today = datetime.now().strftime('%Y%m%d')
output_file = output_dir / f"audit_{today}.md"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"# Airtable データ品質監査\n\n")
    f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"対象レコード数: {len(shops)}\n\n")

    # 【1】説明文の取り違え
    f.write(f"## 【1】説明文の取り違え\n\n")
    f.write(f"該当件数: {len(mismatched_desc)}\n\n")
    if mismatched_desc:
        for item in mismatched_desc:
            f.write(f"- **{item['id']}** / {item['name']} / 含まれている店名: {', '.join(item['found_names'])}\n")
    f.write("\n")

    # 【2】定型文の混入
    f.write(f"## 【2】定型文の混入\n\n")
    f.write(f"該当件数（ユニーク定型文）: {len(duplicated_texts)}\n\n")
    if duplicated_texts:
        for text, count in duplicated_texts.items():
            f.write(f"- 出現回数 {count} 回: {text[:60]}...\n")
    f.write("\n")

    # 【3】重複レコード
    f.write(f"## 【3】重複レコード\n\n")
    f.write(f"### 電話番号重複\n")
    f.write(f"グループ数: {len(dup_phones)}\n\n")
    if dup_phones:
        for phone, shops_list in sorted(dup_phones.items()):
            f.write(f"- **{phone}** ({len(shops_list)}件)\n")
            for shop in shops_list:
                f.write(f"  - {shop['id']} / {shop['name']}\n")
    f.write("\n")

    f.write(f"### 住所重複\n")
    f.write(f"グループ数: {len(dup_addresses)}\n\n")
    if dup_addresses:
        for addr, shops_list in sorted(dup_addresses.items()):
            f.write(f"- **{addr}** ({len(shops_list)}件)\n")
            for shop in shops_list:
                f.write(f"  - {shop['id']} / {shop['name']}\n")
    f.write("\n")

    # 【4】タグの整合性
    f.write(f"## 【4】タグの整合性\n\n")
    f.write(f"該当件数: {len(tag_issues)}\n\n")
    if tag_issues:
        for item in tag_issues:
            f.write(f"- {item['id']} / {item['name']} / {item['issue']}\n")
    f.write("\n")

    # 【5】エリアと住所の不一致
    f.write(f"## 【5】エリアと住所の不一致\n\n")
    f.write(f"該当件数: {len(area_mismatch)}\n\n")
    if area_mismatch:
        for item in area_mismatch:
            f.write(f"- {item['id']} / {item['name']}\n")
            f.write(f"  エリア: {item['area']} / 住所: {item['address']}\n")
    f.write("\n")

    # 【6】必須フィールドの欠損
    f.write(f"## 【6】必須フィールドの欠損\n\n")
    f.write(f"該当件数: {len(missing_fields)}\n\n")
    if missing_fields:
        for item in missing_fields:
            f.write(f"- {item['id']} / {item['name']} / 欠損: {item['missing']}\n")
    f.write("\n")

    # 【7】シーンタグの妥当性
    f.write(f"## 【7】シーンタグの妥当性\n\n")
    f.write(f"### シーンタグなし\n")
    f.write(f"件数: {len(no_scene_tags)}\n\n")
    if no_scene_tags:
        for item in no_scene_tags:
            f.write(f"- {item['id']} / {item['name']}\n")
    f.write("\n")

    f.write(f"### ランチありなのに食事がない\n")
    f.write(f"件数: {len(lunch_without_food)}\n\n")
    if lunch_without_food:
        for item in lunch_without_food:
            f.write(f"- {item['id']} / {item['name']} / {item['menu']}\n")

print(f"\n✅ 監査完了: {output_file}")
