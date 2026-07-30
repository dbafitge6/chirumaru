#!/usr/bin/env python3
"""
Obsidian の「chirumaru-追加店舗リスト.md」から店舗情報を読み込み、
Airtable に登録するスクリプト
"""

import re
from pathlib import Path
from datetime import datetime

def read_obsidian_list():
    """Obsidian ファイルから未処理の店舗リストを抽出"""
    obsidian_file = Path.home() / "Documents/Obsidian Vault/chirumaru-追加店舗リスト.md"

    if not obsidian_file.exists():
        print(f"❌ ファイルが見つかりません: {obsidian_file}")
        return []

    with open(obsidian_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 「未処理（新規追加待ち）」セクションから店舗名を抽出
    match = re.search(
        r"## 未処理（新規追加待ち）\n\n```\n(.*?)\n```",
        content,
        re.DOTALL
    )

    if not match:
        print("⚠️  「未処理」セクションが見つかりません")
        return []

    shops_text = match.group(1)
    shops = [line.strip("- ").strip() for line in shops_text.split("\n") if line.strip().startswith("- ")]
    shops = [s for s in shops if s and not s.startswith("形式:") and not s.startswith("例：")]

    return shops

def update_obsidian_status(shop_name, status, airtable_id=None):
    """Obsidian ファイルのステータスを更新"""
    obsidian_file = Path.home() / "Documents/Obsidian Vault/chirumaru-追加店舗リスト.md"

    with open(obsidian_file, "r", encoding="utf-8") as f:
        content = f.read()

    if status == "completed" and airtable_id:
        # 完了セクションに追加
        completed_entry = f"| {shop_name} | {datetime.now().strftime('%Y-%m-%d')} | {airtable_id} | ✅ |"

        # テンプル行の後に追加
        content = re.sub(
            r"(\| （完了した店舗がここに一覧表示されます） \| \| \| \|)",
            f"{completed_entry}\n\\1",
            content
        )

        print(f"✅ {shop_name} を「完了」に移動しました")

    with open(obsidian_file, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    print("📖 Obsidian から追加店舗リストを読み込み中...\n")

    shops = read_obsidian_list()

    if not shops:
        print("⚠️  処理対象の店舗がありません")
        print("    「chirumaru-追加店舗リスト.md」の「未処理」セクションに店舗名を追加してください")
        return

    print(f"📋 検出された店舗数: {len(shops)}\n")

    for i, shop_name in enumerate(shops, 1):
        print(f"【{i}】{shop_name}")

    print("\n" + "="*50)
    print("📊 次のステップ:")
    print("1. store-researcher エージェントで各店舗を調査")
    print("2. 住所・電話・営業時間・タグを取得")
    print("3. Airtable に登録")
    print("4. Obsidian を「完了」に更新")
    print("="*50 + "\n")

    # ここで store-researcher エージェントを呼び出す
    # (実装は以下を参照)

    return shops

if __name__ == "__main__":
    shops = main()
