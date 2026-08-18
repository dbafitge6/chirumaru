#!/usr/bin/env python3
"""
ちるまる Instagram 自動投稿システム
2日ごとに異なる3店舗を選択 → Postiz経由で投稿
"""

import os
import json
import random
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap

# .env ファイルを読み込む
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# 環境変数
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
FORCE_SCENE = os.environ.get("FORCE_SCENE", None)  # シーン固定指定

# 設定
BASE_ID = "appyyoKM7RprQRht8"
TABLE_NAME = "Stores"
AIRTABLE_TOKEN = os.environ.get("AIRTABLE_TOKEN")
POSTIZ_API_KEY = os.environ.get("POSTIZ_API_KEY")
print(f"DEBUG: AIRTABLE_TOKEN={'*' * 10 if AIRTABLE_TOKEN else 'EMPTY'}")
print(f"DEBUG: POSTIZ_API_KEY={'*' * 10 if POSTIZ_API_KEY else 'EMPTY'}")
print(f"DEBUG: All env keys with 'AIRTABLE' or 'POSTIZ': {[k for k in os.environ.keys() if 'AIRTABLE' in k or 'POSTIZ' in k]}")
INSTAGRAM_INTEGRATION_ID = "cmsopxrcz024opo0ygfgl0m4q"
VIDEO_URL = "https://uploads.postiz.com/Dw9DWadyRH.mp4"

# BGM設定（新しい音源）
BGM_PATH = Path(__file__).parent.parent / "assets" / "alex-morgan-cafe-jazz-coffee-shop-music-564287.mp3"

# Canva テンプレート設定
CANVA_DESIGN_ID = "DAHSK0_hc5A"  # ちるまる Reels雛形 1080x1920
CANVA_ELEMENTS = {
    # 1ページ目（フック）/ PBfyCFl2pBn7QNmd
    "hook_text": "PBfyCFl2pBn7QNmd-LBBvKWDGpp6csKzK",
    "hook_sub": "PBfyCFl2pBn7QNmd-LBSgvfdCL0lnd9cZ",
    # 2ページ目（店舗1） / PBqVhyVm5VZBqq2J
    "shop1_name": "PBqVhyVm5VZBqq2J-LBN2PjYbr7rLKj1j",
    "shop1_area": "PBqVhyVm5VZBqq2J-LB2tJn0654FmjMDD",
    "shop1_desc": "PBqVhyVm5VZBqq2J-LBQL9Y1HXNB1h6lq",
    # 3ページ目（店舗2） / PBMph17dQC5LVtgs
    "shop2_name": "PBMph17dQC5LVtgs-LBkBvFdcHQfXSgnz",
    "shop2_area": "PBMph17dQC5LVtgs-LBxRW3lvN66stQYB",
    "shop2_desc": "PBMph17dQC5LVtgs-LBxvXsmdCdJJFkrX",
    # 4ページ目（店舗3） / PBD7pRFZfg5GZ8SC
    "shop3_name": "PBD7pRFZfg5GZ8SC-LB5mZmjPrxy84ws2",
    "shop3_area": "PBD7pRFZfg5GZ8SC-LBx0Y1QBLJtmZKrq",
    "shop3_desc": "PBD7pRFZfg5GZ8SC-LBhjR5lmCdY9lBZG",
    # 5ページ目（CTA） / PBn4T0bT45BZ0Y8h（固定・差し込みなし）
}

if not AIRTABLE_TOKEN:
    print("❌ エラー: AIRTABLE_TOKEN が設定されていません")
    sys.exit(1)

if not DRY_RUN and not POSTIZ_API_KEY:
    print("❌ エラー: ドライランモード以外では POSTIZ_API_KEY が必要です")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent.parent / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SLIDES_DIR = Path(__file__).parent.parent / "generated_slides"
SLIDES_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = OUTPUT_DIR / "instagram_post_history.json"
FRANCHISE_CHAINS = ['ドトール', 'タリーズ', 'スターバックス', 'コメダ']

# 誤字辞書
TYPO_MAP = {
    '情緒い': '情緒あ',
    '穿場': '穴場',
    '弌彦': '弥彦',
}

# ネガティブ語リスト
NEGATIVE_WORDS = ['不快', 'まずい', '汚い', '最悪', 'ひどい', '残念']

# 投稿済み店舗・シーンの記録
POSTED_STORES_FILE = Path(__file__).parent.parent / "data" / "posted_stores.json"
POSTED_SCENES_FILE = Path(__file__).parent.parent / "data" / "posted_scenes.json"
POSTED_STORES_FILE.parent.mkdir(parents=True, exist_ok=True)

def fix_typos(text):
    """テキストから誤字を修正"""
    for typo, correct in TYPO_MAP.items():
        text = text.replace(typo, correct)
    text = text.replace('/', '・')  # Canva表示バグの対策
    return text


def check_content_safety(text):
    """コンテンツの安全性チェック"""
    if '/' in text:
        raise ValueError(f"❌ エラー: テキストに '/' が含まれています（Canva表示バグの原因）\n{text}")

    for word in NEGATIVE_WORDS:
        if word in text:
            raise ValueError(f"❌ エラー: ネガティブ語 '{word}' が検出されました\n投稿を中止します\n{text}")

def get_media_duration(filepath):
    """メディアファイルの長さを秒単位で取得"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1", filepath],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️  メディア長取得エラー: {e}")
        return 0

def compose_with_bgm(video_path, bgm_path, output_path):
    """BGMを挿入した動画を作成

    Args:
        video_path: 元の動画ファイルパス
        bgm_path: BGM音源ファイルパス
        output_path: 出力先ファイルパス

    Returns:
        出力ファイルパス
    """
    print(f"\n🎵 BGM 合成中...")

    # 動画とBGMの長さを取得
    video_duration = get_media_duration(str(video_path))
    bgm_duration = get_media_duration(str(bgm_path))

    if video_duration <= 0 or bgm_duration <= 0:
        print(f"⚠️  メディア長取得失敗、BGM挿入をスキップ")
        return video_path

    # ランダム開始位置を計算（BGM が最後まで再生される範囲内）
    max_start = max(0, bgm_duration - video_duration)
    random_start = random.uniform(0, max_start) if max_start > 0 else 0

    print(f"  動画長: {video_duration:.1f}s")
    print(f"  BGM長: {bgm_duration:.1f}s")
    print(f"  BGM開始位置: {random_start:.1f}s（範囲: 0-{max_start:.1f}s）")

    # FFmpeg コマンド構築
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-ss", str(random_start),
        "-i", str(bgm_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-af", "afade=t=in:st=0:d=0.5,afade=t=out:st={}:d=0.5".format(video_duration - 0.5),
        "-y",
        str(output_path)
    ]

    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"❌ FFmpeg エラー: {result.stderr}")
            return video_path
        print(f"✅ BGM 合成完了: {output_path}")
        return Path(output_path)
    except subprocess.TimeoutExpired:
        print(f"❌ FFmpeg タイムアウト")
        return video_path
    except Exception as e:
        print(f"❌ BGM 合成エラー: {e}")
        return video_path

def draw_text_with_wrapping(draw, text, xy, font, fill, max_width, max_height=None, line_spacing=1.35, align="center", font_name="bold"):
    """テキスト折り返しと自動フォントサイズ縮小を行い、テキストを描画

    【修正】フォント縮小時に新しい ImageFont を作成して描画

    Args:
        draw: ImageDraw オブジェクト
        text: 描画するテキスト
        xy: (center_x, top_y) または (left_x, top_y)
        font: ImageFont オブジェクト
        fill: 文字色
        max_width: 最大幅（ピクセル）
        max_height: 最大高さ（指定時のみ自動縮小を実行）
        line_spacing: 行間（1.0 = フォントサイズ）
        align: "center" または "left"
        font_name: フォント名（"bold" または "medium"）— 縮小時の再作成に使用

    Returns:
        (テキストが占める高さ, 使用したフォント)
    """
    x_pos, top_y = xy
    current_font = font
    original_font_size = font.size

    def wrap_text(text, font, max_width):
        """テキストを折り返す（textbbox の実測幅で判定）"""
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append('')
                continue

            current_line = ''
            for char in paragraph:
                test_line = current_line + char
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]

                if line_width > max_width:
                    if current_line:
                        lines.append(current_line)
                        current_line = char
                    else:
                        lines.append(char)
                else:
                    current_line = test_line

            if current_line:
                lines.append(current_line)

        return lines

    # テキストを折り返す
    lines = wrap_text(text, current_font, max_width)

    # 高さを計算
    line_height = int(original_font_size * line_spacing)
    total_height = line_height * len(lines)

    # max_height が指定されている場合、フォントサイズを縮小
    final_font = current_font
    final_line_height = line_height
    final_total_height = total_height

    if max_height and total_height > max_height:
        scale_factor = max_height / total_height
        new_font_size = max(8, int(original_font_size * scale_factor))

        # 新しい ImageFont を作成
        try:
            final_font, _ = load_font(font_name, new_font_size)
            final_line_height = int(new_font_size * line_spacing)
            final_total_height = final_line_height * len(lines)
        except Exception as e:
            print(f"⚠️  フォント縮小失敗: {e}")
            final_font = current_font
            final_line_height = line_height
            final_total_height = total_height

    # テキストを描画
    current_y = top_y
    for line in lines:
        if line:
            if align == "center":
                draw.text((x_pos, current_y + final_line_height // 2), line, font=final_font, fill=fill, anchor="mm")
            else:
                draw.text((x_pos, current_y + final_line_height // 2), line, font=final_font, fill=fill, anchor="lm")
        current_y += final_line_height

    return final_total_height, final_font

def load_font(font_name, size):
    """フォントを読み込む（Zen Maru Gothic）

    Args:
        font_name: "bold" (ZenMaruGothic-Bold) or "medium" (ZenMaruGothic-Medium)
        size: フォントサイズ

    Returns:
        (ImageFont オブジェクト, 使用されたフォントパス)
    """
    font_dir = Path(__file__).parent.parent / "assets" / "fonts"

    # Zen Maru Gothic ファイル名
    if font_name == "bold":
        font_filename = "ZenMaruGothic-Bold.ttf"
    else:  # "medium" or その他は Medium を使う
        font_filename = "ZenMaruGothic-Medium.ttf"

    font_path = font_dir / font_filename

    if font_path.exists():
        try:
            font = ImageFont.truetype(str(font_path), size)
            return font, str(font_path)
        except OSError as e:
            raise Exception(f"❌ フォントファイルが破損しています: {font_path}\nエラー: {e}")
    else:
        raise Exception(f"❌ Zen Maru Gothic TTF が見つかりません\n期待値: {font_path}\n確認済みファイル:\n  - {font_dir / 'ZenMaruGothic-Bold.ttf'}\n  - {font_dir / 'ZenMaruGothic-Medium.ttf'}")

def generate_slides(hook_text, shops):
    """Pillow で 5枚のスライドを生成

    Args:
        hook_text: フック文
        shops: [{'name': ..., 'area': ..., 'desc': ...}, ...]

    Returns:
        [slide_path1, slide_path2, ...]
    """
    print("\n🎨 スライド画像を生成中...")

    # フォントを読み込む
    try:
        font_bold, font_bold_path = load_font("bold", 112)
        font_bold_92, _ = load_font("bold", 92)
        font_bold_76, _ = load_font("bold", 76)
        font_medium_54, _ = load_font("medium", 54)
        font_medium_52, _ = load_font("medium", 52)
        font_medium_48, _ = load_font("medium", 48)
        font_medium_46, _ = load_font("medium", 46)
        font_medium_56, _ = load_font("medium", 56)
        font_medium_42, font_medium_path = load_font("medium", 42)

        print(f"✅ フォント読み込み成功")
        print(f"   Bold: {font_bold_path}")
        print(f"   Medium: {font_medium_path}")
    except Exception as e:
        print(str(e))
        sys.exit(1)

    # ロゴを読み込む（外部ファイルが必須）
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    if not logo_path.exists():
        print(f"❌ ロゴファイルが見つかりません: {logo_path}")
        print(f"   assets/logo.png を配置してください")
        sys.exit(1)

    try:
        logo = Image.open(logo_path).convert("RGBA")
    except Exception as e:
        print(f"❌ ロゴファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

    slides = []

    # 【1枚目 フック】
    slide1 = Image.new("RGB", (1080, 1920), "#5C4139")
    draw1 = ImageDraw.Draw(slide1)

    # ロゴを左上 (55,55) に 190x190 で配置
    logo_resized = logo.resize((190, 190), Image.Resampling.LANCZOS)
    slide1.paste(logo_resized, (55, 55), logo_resized)

    # タグライン（左揃え、x=285、ロゴの右側）
    tagline = "新潟のカフェ・パン屋・スイーツ探し"
    draw_text_with_wrapping(draw1, tagline, (285, 118), font_medium_42, "#C9A392", 500, align="left", font_name="medium")

    # フック文（中央、y=760 が上端、幅900で中央x=540）
    draw_text_with_wrapping(draw1, hook_text, (540, 760), font_bold, "#F7EDE5", 900, max_height=320, line_spacing=1.35, align="center", font_name="bold")

    # サブテキスト
    draw1.text((540, 1140), "新潟のカフェ 384軒から", font=font_medium_54, fill="#DCB8AA", anchor="mm")

    slides.append(slide1)

    # 【2〜4枚目 店舗】
    for i, shop in enumerate(shops):
        slide = Image.new("RGB", (1080, 1920), "#FBF1EA")
        draw = ImageDraw.Draw(slide)

        # ロゴ（モノトーン版）
        logo_mono = logo.resize((190, 190), Image.Resampling.LANCZOS)
        slide.paste(logo_mono, (55, 55), logo_mono)

        # タグライン（左揃え、x=285）
        draw_text_with_wrapping(draw, tagline, (285, 118), font_medium_42, "#B4B4B4", 500, align="left", font_name="medium")

        # 店名（y=700 が上端、幅900で中央x=540）- 積み上げ式計算開始
        shop_name_height, _ = draw_text_with_wrapping(draw, shop['name'], (540, 700), font_bold_92, "#7A5A4C", 900, max_height=140, line_spacing=1.35, align="center", font_name="bold")

        # エリア（店名の下端 + 40px）
        area_y = 700 + shop_name_height + 40
        area_height, _ = draw_text_with_wrapping(draw, shop['area'], (540, area_y), font_medium_48, "#C09A88", 900, max_height=100, line_spacing=1.35, align="center", font_name="medium")

        # 一言（エリアの下端 + 90px、幅840で中央x=540）
        # 一言が空の場合は描画をスキップ
        if shop['desc']:
            desc_y = area_y + area_height + 90
            draw_text_with_wrapping(draw, shop['desc'], (540, desc_y), font_medium_52, "#8A6A5C", 840, max_height=400, line_spacing=1.6, align="center", font_name="medium")

        slides.append(slide)

    # 【5枚目 CTA】
    slide5 = Image.new("RGB", (1080, 1920), "#FBF1EA")
    draw5 = ImageDraw.Draw(slide5)

    # ロゴを中央に 620x617 / (230, 250)
    logo_large = logo.resize((620, 617), Image.Resampling.LANCZOS)
    slide5.paste(logo_large, (230, 250), logo_large)

    # テキスト1（y=980 が上端）
    draw_text_with_wrapping(draw5, "新潟のカフェ 384軒\nまとめてます", (540, 980), font_bold_76, "#7A5A4C", 900, max_height=200, line_spacing=1.35, align="center", font_name="bold")

    # テキスト2（y=1290 が上端）
    draw_text_with_wrapping(draw5, "保存して、次の休みに", (540, 1290), font_medium_56, "#C09A88", 900, max_height=120, line_spacing=1.35, align="center", font_name="medium")

    # テキスト3（y=1460 が上端）
    draw_text_with_wrapping(draw5, "https://www.chirumaru.jp/", (540, 1460), font_medium_46, "#C09A88", 900, max_height=80, line_spacing=1.35, align="center", font_name="medium")

    slides.append(slide5)

    # スライドを PNG で保存
    slide_paths = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    print("\n【スライド PNG】")
    for i, slide in enumerate(slides, 1):
        slide_path = SLIDES_DIR / f"slide_{i:02d}_{timestamp}.png"
        slide.save(slide_path)
        slide_paths.append(slide_path)
        print(f"  {i}. {slide_path}")

    return slide_paths

def slides_to_video(slide_paths, output_path):
    """スライドを MP4 動画に変換

    Args:
        slide_paths: PNG ファイルパスのリスト
        output_path: 出力 MP4 パス

    Returns:
        出力ファイルパス
    """
    print(f"\n🎬 MP4 動画を生成中（{len(slide_paths)}スライド × 3秒 = {len(slide_paths)*3}秒）...")

    try:
        # FFmpeg で連結
        # 各スライドを3秒表示
        # 注意: FFmpeg concat demuxer は最後のエントリの duration を無視するため、
        # 最後のスライドをもう一度追加する
        concat_list = []
        for slide_path in slide_paths:
            concat_list.append(f"file '{slide_path}'")
            concat_list.append("duration 3")

        # 最後のスライドをもう一度追加（duration なし）
        if slide_paths:
            concat_list.append(f"file '{slide_paths[-1]}'")

        concat_file = Path("/tmp/concat_list.txt")
        with open(concat_file, 'w') as f:
            f.write('\n'.join(concat_list))

        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-pix_fmt", "yuv420p",
            "-y",
            str(output_path)
        ]

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"❌ FFmpeg エラー: {result.stderr}")
            return None

        print(f"✅ MP4 生成完了")
        print(f"   {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ 動画化エラー: {e}")
        return None

print("=" * 70)
print("🎬 Instagram 自動投稿システム開始")
print("=" * 70)

# Step 1: Airtable からシーンを選択し、該当店舗を取得
print("\n【Step 1】シーン単位で店舗を選択")
print("=" * 70)

url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}

# シーンと対応するキャプション（状況系）
SITUATION_SCENES = {
    '日曜営業': '日曜も開いてる新潟のカフェ、3軒',
    '夜まで営業': '夕方からでも間に合うカフェ',
    'ランチあり': 'ちゃんとごはんが食べられるカフェ',
    'テイクアウト可': '持ち帰りできるカフェ'
}

# 名物カテゴリと対応するフック文
SPECIALTY_CAPTIONS = {
    'かき氷': '新潟のかき氷、まだ間に合う',
    'プリン': 'プリンが本気の店、あります',
    'チーズケーキ': 'チーズケーキで選ぶなら',
    'パンケーキ': '休日の朝はパンケーキ',
    'ドーナツ': 'ドーナツ目当てで行きたい',
    'クレープ': 'クレープが主役の店',
    'ハンバーガー': '新潟のバーガー、侮れない',
    'パン': 'パン目当てのドライブ',
    'パスタ': 'カフェのパスタが本格的',
    'ケーキ': 'ケーキが名物のカフェ'
}

SCENE_CAPTIONS = {**SITUATION_SCENES, **{k: v for k, v in SPECIALTY_CAPTIONS.items()}}

all_records = []
offset = None

try:
    while True:
        params = {"returnFieldsByFieldId": "true"} if not offset else {"offset": offset, "returnFieldsByFieldId": "true"}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ API エラー: {response.status_code}")
            sys.exit(1)

        data = response.json()
        all_records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset:
            break

    print(f"✅ 取得完了: {len(all_records)} 店舗")

    # フランチャイズ除外（フィールドID ベース）
    shops_list = []
    for record in all_records:
        fields = record.get('fields', {})
        name = fields.get('fldpEdbx8RE5XfBln', 'Unknown')  # Store Name
        is_franchise = any(chain in name for chain in FRANCHISE_CHAINS)

        if not is_franchise:
            # 一言を取得（Airtable から直接）
            tagline = fields.get('fldZTL8r12En3D6eF', '')  # 一言
            # 記号置換を早期に実施（安全性チェック前）
            tagline = tagline.replace('/', '・') if tagline else ''

            shops_list.append({
                'id': record['id'],
                'name': name,
                'area': fields.get('fld6sCx8y2OxZV5So', 'Unknown'),  # Area
                'tagline': tagline,  # 一言（Airtable から直接取得）
                'tags': fields.get('fldDl6OsS4EKmJT18', []),  # Scene Tags
                'existing_tags': fields.get('fldsh2ess7aYHhJ8e', '')  # Existing Tags
            })

    print(f"✅ フランチャイズ除外: {len(shops_list)} 店舗")

    # 投稿済み店舗を除外
    posted_store_ids = set()
    if POSTED_STORES_FILE.exists():
        with open(POSTED_STORES_FILE, 'r', encoding='utf-8') as f:
            posted_list = json.load(f)
            posted_store_ids = {item['id'] for item in posted_list}

    # 全店舗が投稿済みになったらリセット
    if len(posted_store_ids) >= len(shops_list):
        print(f"\n🔄 全店舗の投稿が完了しました（{len(posted_store_ids)}/{len(shops_list)}）")
        print("📌 投稿済み記録をリセットしています...\n")
        posted_store_ids = set()
        POSTED_STORES_FILE.write_text('[]', encoding='utf-8')

    # 投稿済みシーンから直近3回を除外
    excluded_scenes = set()
    if POSTED_SCENES_FILE.exists():
        with open(POSTED_SCENES_FILE, 'r', encoding='utf-8') as f:
            posted_scenes_list = json.load(f)
            # 直近3回を取得
            if len(posted_scenes_list) > 0:
                excluded_scenes = {item['scene'] for item in posted_scenes_list[-3:]}

    # シーン選択ロジック
    selected_scene = None
    selected_3 = []
    attempts = 0
    max_attempts = len(SCENE_CAPTIONS) * 2

    # FORCE_SCENE が指定されている場合
    if FORCE_SCENE:
        if FORCE_SCENE not in SCENE_CAPTIONS:
            print(f"❌ エラー: シーン「{FORCE_SCENE}」は存在しません")
            print(f"利用可能なシーン: {', '.join(SCENE_CAPTIONS.keys())}")
            sys.exit(1)

        selected_scene = FORCE_SCENE
        print(f"ℹ️  シーン固定指定: {selected_scene}")

        # シーンに応じた店舗の抽出
        if selected_scene in SITUATION_SCENES:
            # 状況系シーン（シーンタグマッチ）
            scene_shops = [s for s in shops_list if selected_scene in s['tags'] and s['id'] not in posted_store_ids]
        else:
            # 名物系シーン（既存タグマッチ）
            specialty_keyword = selected_scene
            # 既存タグを "/" で分割してリスト化し、完全一致判定
            scene_shops = [s for s in shops_list
                          if specialty_keyword in [t.strip() for t in s['existing_tags'].split('/')] and s['id'] not in posted_store_ids]

        if len(scene_shops) >= 3:
            selected_3 = random.sample(scene_shops, 3)
        else:
            print(f"❌ エラー: シーン「{selected_scene}」に該当する店舗が{len(scene_shops)}軒しかありません（3軒必要）")
            sys.exit(1)

    else:
        # 除外対象を除いたシーンから選ぶ
        available_scenes_filtered = [s for s in SCENE_CAPTIONS.keys() if s not in excluded_scenes]

        # 除外後に候補がなければ全シーンから選ぶ
        if not available_scenes_filtered:
            available_scenes_filtered = list(SCENE_CAPTIONS.keys())

        while not selected_3 and attempts < max_attempts:
            selected_scene = random.choice(available_scenes_filtered)

            # シーンに応じた店舗の抽出
            if selected_scene in SITUATION_SCENES:
                # 状況系シーン（シーンタグマッチ）
                scene_shops = [s for s in shops_list if selected_scene in s['tags'] and s['id'] not in posted_store_ids]
            else:
                # 名物系シーン（既存タグマッチ）
                specialty_keyword = selected_scene
                # 既存タグを "/" で分割してリスト化し、完全一致判定
                scene_shops = [s for s in shops_list
                              if specialty_keyword in [t.strip() for t in s['existing_tags'].split('/')] and s['id'] not in posted_store_ids]

            if len(scene_shops) >= 3:
                selected_3 = random.sample(scene_shops, 3)
            else:
                attempts += 1

        if not selected_3:
            print("❌ エラー: 該当するシーンの店舗が不足しています")
            sys.exit(1)

    print(f"\n🎯 選ばれたシーン: {selected_scene}")
    print(f"🎯 今回選択した 3 店舗:")
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

# Step 2: キャプション作成（シーン単位、誤字修正・安全性チェック含む）
print("\n【Step 2】キャプション作成")
print("=" * 70)

caption_lines = [
    f"🌟 {SCENE_CAPTIONS[selected_scene]} 🌟",
    "",
]
for i, s in enumerate(selected_3, 1):
    caption_lines.append(f"{s['name']}")
    caption_lines.append(f"📍 {s['area']}")
    if s.get('tagline'):
        tagline = fix_typos(s['tagline'])
        caption_lines.append(f"{tagline}")
    caption_lines.append("")

caption_lines.extend([
    "ちるまるで2日おきに新しいお店を紹介🎉",
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

# 安全性チェック
print("\n【Step 2.5】コンテンツ安全性チェック")
print("=" * 70)
try:
    check_content_safety(caption)
    for shop in selected_3:
        check_content_safety(shop['name'])
        if shop.get('tagline'):
            check_content_safety(shop['tagline'])
    print("✅ 安全性チェック合格")
except ValueError as e:
    print(str(e))
    sys.exit(1)

# Step 3: スライド画像を生成
print("\n【Step 3】スライド画像を生成")
print("=" * 70)

# フック文
hook_text = SCENE_CAPTIONS[selected_scene]
print(f"hook_text / {hook_text}")

# 3店舗のデータを準備
shops = []
for i, shop in enumerate(selected_3, 1):
    shop_name = fix_typos(shop['name'])
    shop_area = fix_typos(shop['area'])

    # 一言（Airtable から直接取得）
    shop_desc = fix_typos(shop.get('tagline', ''))

    shops.append({
        'name': shop_name,
        'area': shop_area,
        'desc': shop_desc
    })

    print(f"shop{i}_name / {shop_name} ({len(shop_name)}文字)")
    print(f"shop{i}_area / {shop_area} ({len(shop_area)}文字)")
    print(f"shop{i}_desc / {shop_desc} ({len(shop_desc)}文字)")

# Pillow でスライドを生成
slide_paths = generate_slides(hook_text, shops)

# Step 3.5: スライドを MP4 に変換
print("\n【Step 3.5】スライドを MP4 に変換")
print("=" * 70)

video_path = OUTPUT_DIR / f"chirumaru_slides_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
slides_to_video(slide_paths, str(video_path))

# Step 3.6: BGM 合成
print("\n【Step 3.6】BGM 合成")
print("=" * 70)
if DRY_RUN:
    print("⚠️  ドライランモード（BGM合成スキップ）")
    final_video_path = video_path
else:
    if video_path and BGM_PATH.exists():
        output_bgm_path = OUTPUT_DIR / f"chirumaru_with_bgm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        final_video_path = compose_with_bgm(str(video_path), str(BGM_PATH), str(output_bgm_path))
    else:
        print(f"⚠️  BGM ファイルが見つかりません: {BGM_PATH}")
        final_video_path = video_path

# Step 4: Postiz で投稿（ドライランモードでスキップ可能）
print("\n【Step 4】Postiz で投稿")
print("=" * 70)

if DRY_RUN:
    print("⚠️  ドライランモード（投稿スキップ）")
    print(f"✅ シーン「{selected_scene}」の記録（ドライランのため実際には保存せず）")
else:
    try:
        # Step 4.1: 合成ビデオを Postiz にアップロード
        print("\n📤 ビデオを Postiz にアップロード中...")
        upload_cmd = ['postiz', 'upload', str(final_video_path)]
        upload_result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=120)

        if upload_result.returncode != 0:
            print(f"❌ Postiz アップロード失敗")
            print(f"stderr: {upload_result.stderr}")
            sys.exit(1)

        # アップロード結果から URL を抽出
        # JSON 部分だけを抽出（メッセージが前置きされているため）
        output_lines = upload_result.stdout.strip().split('\n')
        json_start = -1
        for i, line in enumerate(output_lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        if json_start == -1:
            print(f"❌ Postiz レスポンスが JSON でない")
            print(f"レスポンス: {upload_result.stdout}")
            sys.exit(1)

        json_str = '\n'.join(output_lines[json_start:])
        upload_data = json.loads(json_str)
        postiz_video_url = upload_data.get('path')
        if not postiz_video_url:
            print(f"❌ Postiz URL が取得できません")
            print(f"レスポンス: {upload_result.stdout}")
            sys.exit(1)

        print(f"✅ アップロード完了: {postiz_video_url}")

        # Step 4.2: Postiz API で投稿作成
        print("\n📱 Instagram に投稿中...")
        now_utc = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        postiz_cmd = [
            'postiz', 'posts:create',
            '-c', caption,
            '-m', postiz_video_url,
            '-s', now_utc,
            '--settings', '{"post_type":"post"}',
            '-i', INSTAGRAM_INTEGRATION_ID
        ]

        result = subprocess.run(postiz_cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ 投稿成功！")
            print(result.stdout)

            # 投稿履歴を記録（店舗とシーン）
            today = datetime.now().strftime("%Y-%m-%d")

            # 店舗の記録
            posted_data = []
            if POSTED_STORES_FILE.exists():
                with open(POSTED_STORES_FILE, 'r', encoding='utf-8') as f:
                    posted_data = json.load(f)

            for shop in selected_3:
                posted_data.append({
                    "id": shop['id'],
                    "name": shop['name'],
                    "date": today
                })

            with open(POSTED_STORES_FILE, 'w', encoding='utf-8') as f:
                json.dump(posted_data, f, ensure_ascii=False, indent=2)

            # シーンの記録
            posted_scenes_data = []
            if POSTED_SCENES_FILE.exists():
                with open(POSTED_SCENES_FILE, 'r', encoding='utf-8') as f:
                    posted_scenes_data = json.load(f)

            posted_scenes_data.append({
                "scene": selected_scene,
                "date": today
            })

            with open(POSTED_SCENES_FILE, 'w', encoding='utf-8') as f:
                json.dump(posted_scenes_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 投稿履歴を {POSTED_STORES_FILE} に記録しました")

            # Git コミット＆プッシュで永続化
            try:
                subprocess.run(['git', 'add', str(POSTED_STORES_FILE), str(POSTED_SCENES_FILE)], cwd=Path(__file__).parent.parent, check=True, capture_output=True)
                subprocess.run([
                    'git', 'commit', '-m',
                    f"Update: add posted stores and scene ({today})",
                    '--author', 'Claude Code <noreply@anthropic.com>'
                ], cwd=Path(__file__).parent.parent, check=True, capture_output=True)
                subprocess.run(['git', 'push', 'github', 'main'], cwd=Path(__file__).parent.parent, check=True, capture_output=True, timeout=30)
                print(f"✅ Git コミット＆プッシュ完了")
            except Exception as git_e:
                print(f"⚠️  Git 操作エラー（投稿は成功）: {git_e}")

        else:
            print(f"❌ Postiz エラー")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print(f"❌ エラー: Postiz コマンドがタイムアウト（30秒以上）")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

print("\n" + "=" * 70)
if DRY_RUN:
    print("✅ ドライラン完了（投稿は実行されていません）")
else:
    print("✅ 自動投稿完了！")
print("=" * 70)
