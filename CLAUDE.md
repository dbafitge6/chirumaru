@AGENTS.md

# ちるまるプロジェクト — 現在の状態

## 🔄 進行中のプロジェクト（2026-08-13）

### Instagram 自動投稿システム
**状態**: 実装中（修正段階）

**要件**:
- ✅ 投稿形式: Reels（動画 MP4）
- ✅ BGM: jazz background（YouTube から取得、FFmpeg で合成）
- ✅ ツール: Postiz（自動スケジュール）
- ✅ **毎回異なる店舗を自動選択**（Airtable からランダム選択、前回の 3 店舗を除外）
- ✅ 誤字見直し自動実行（情緒い→情緒あ、穿場→穴場など）
- ✅ 投稿周期: 2 日おき（最初の投稿から）

**現在の状態**:
- 🔴 GitHub Actions で Postiz CLI がインストールされていなかった（2026-08-13 修正）
- ✅ ワークフロー修正完了（`npm install -g postiz` 追加）
- ✅ スクリプト完成（`scripts/auto_instagram_post.py`）
  - Airtable から 3 店舗をランダム選択
  - 前回の店舗を自動除外
  - キャプション生成（説明文から動的生成）
  - 誤字見直し機能搭載

**完了したテスト**:
- ✅ Canva テンプレート 5 ページ作成（ロゴ、店舗 3 つ、CTA）
- ✅ YouTube から jazz background ダウンロード
- ✅ FFmpeg で BGM 合成（MP4 + 音声）
- ✅ Postiz にアップロード・投稿作成
- ✅ GitHub Actions ワークフロー修正

**次のステップ**:
1. 今日（2026-08-13）の投稿を新しい 3 店舗で作成
2. 明日（2026-08-15）から 2 日おきに自動投稿開始
3. Airtable に店舗情報を追加するだけで自動投稿される

---

## 作業ルール

**CLAUDE.md 管理**:
- このファイルは「現在の状態」「進行中のタスク」のみを記録
- 完了した作業は削除（git history で参照可能）
- 行数を 150 行以下に保つ
- 重要な要件は必ず記録

**Airtable 操作**:
- 書き込みは実行前に必ずユーザーに確認
- トークン: ***REMOVED***（書き込み権限）

**Instagram Reels 投稿ルール**:
- 形式: Reels（動画）
- BGM: jazz background（固定）
- ツール: Postiz
- エクスポート: MP4（Canva + FFmpeg で BGM 合成）

**自動投稿スクリプト要件**:
- 毎回 Airtable から **異なる 3 店舗を自動選択**（重要！）
- 前回の 3 店舗を除外
- 誤字見直し実行
- キャプション自動生成

---

## 重要なデータ参照

**Airtable**:
- ベース: ちるまる (appyyoKM7RprQRht8)
- テーブル: Stores (tblcOdcqCxzb7kX0e)
- PAT: ***REMOVED***

**Postiz**:
- API Key: ***REMOVED***
- Instagram 統合 ID: cmsopxrcz024opo0ygfgl0m4q
- BGM ビデオ URL: https://uploads.postiz.com/Dw9DWadyRH.mp4

**GitHub Actions**:
- ワークフロー: `.github/workflows/auto_instagram_post.yml`
- スクリプト: `scripts/auto_instagram_post.py`
- トリガー: 毎日 03:00 UTC（12:00 JST）、2 日経過で実行
