@AGENTS.md

<<<<<<< HEAD
# ちるまる

## 状態
- Instagram Reels 自動投稿：稼働中
- GitHub Actions で 2日おきに実行（03:00 UTC / 12:00 JST）
- Airtable に店舗を追加すれば自動で投稿対象になる

## 必ず守ること
- **投稿店舗は毎回 Airtable からランダム選択し、前回の3店舗を除外する**
- Canva に渡すテキストに "/" を含めない（表示バグ）
- ネガティブ語（不快/まずい/汚い/最悪）が入っていたら投稿せず報告
- Airtable への書き込みは実行前に必ず確認
- 完了報告の前に結果を自分で確認する
- **Airtableのレコード処理では毎回最新リストを API 取得してから処理する。過去のログやスクリーンショットのレコード一覧を流用しない**（削除済みレコード混入防止）

## 報告ルール（すべてのスクリプト実行に適用）
- 「完璧」「完了」「正常に動作」などの語を使わない。事実だけ書く
- 統計だけでなく、判定対象の全件を原文とともに表示する
- 期待値と結果が一致しない場合、原因を特定するまで次に進まない

## 環境
- **Airtable**: appyyoKM7RprQRht8 / Stores: tblcOdcqCxzb7kX0e / PAT は GitHub Secrets
- **Postiz**: Instagram統合ID cmsopxrcz024opo0ygfgl0m4q / API Key は GitHub Secrets
- BGM: https://uploads.postiz.com/Dw9DWadyRH.mp4
- ワークフロー: .github/workflows/auto_instagram_post.yml
- スクリプト: scripts/auto_instagram_post.py

## 投稿仕様
- Reels（MP4）、BGM は jazz background 固定、Canva + FFmpeg で合成
- キャプションは Airtable の説明文から生成
- 誤字自動修正（情緒い→情緒あ、穿場→穴場など）

### Canva テンプレート
- **テンプレート**: DAHSK0_hc5A「ちるまる Reels雛形 1080x1920」
  - 1080x1920（Reels形式）
  - 1ページ目（フック）: PBfyCFl2pBn7QNmd
    - フック文: PBfyCFl2pBn7QNmd-LBBvKWDGpp6csKzK
    - サブ: PBfyCFl2pBn7QNmd-LBSgvfdCL0lnd9cZ
  - 2ページ目（店舗1）: PBqVhyVm5VZBqq2J
    - 店名: PBqVhyVm5VZBqq2J-LBN2PjYbr7rLKj1j
    - エリア: PBqVhyVm5VZBqq2J-LB2tJn0654FmjMDD
    - 一言: PBqVhyVm5VZBqq2J-LBQL9Y1HXNB1h6lq
  - 3ページ目（店舗2）: PBMph17dQC5LVtgs
    - 店名: PBMph17dQC5LVtgs-LBkBvFdcHQfXSgnz
    - エリア: PBMph17dQC5LVtgs-LBxRW3lvN66stQYB
    - 一言: PBMph17dQC5LVtgs-LBxvXsmdCdJJFkrX
  - 4ページ目（店舗3）: PBD7pRFZfg5GZ8SC
    - 店名: PBD7pRFZfg5GZ8SC-LB5mZmjPrxy84ws2
    - エリア: PBD7pRFZfg5GZ8SC-LBx0Y1QBLJtmZKrq
    - 一言: PBD7pRFZfg5GZ8SC-LBhjR5lmCdY9lBZG
  - 5ページ目（CTA）: PBn4T0bT45BZ0Y8h（固定・テキスト差し込みなし）

## シーンタグの判定ルール（営業時間から機械判定）
### 日曜営業タグ
- 定休日を抽出し、日曜を含まない場合に付与
- 「無休」「定休なし」「休みなし」等は定休日ゼロとして付与
- 「不定休」「記載なし」は判定不能。タグを付けない
- 営業時間の曜日区分（「日祝10:30-18:00」等）からの推定はしない

### 夜まで営業タグ
- 閉店時刻が19:00以降の場合に付与
- 「翌」を含む深夜営業も対象

### 定休日の抽出
- 「定休」「休」「休館」「休業」「休み」等の休業語とセットで書かれている曜日のみ抽出
- パターン例：「月～木・日定休」「木・日・祝日定休」「定休日: 火曜」
- 営業時間の曜日別区分（「火～金...／土日祝...」）は定休日ではなく営業時間情報

### ランチあり
- キーワード方式では「フルーツサンド」と「ローストビーフサンド」を区別できないため使わない
- メニュー原文を読んで文脈で判定する（Claude Code 自身が判定。API不要）
- 判定基準:
  - 食事あり = 具が食事系のサンドイッチ、パスタ、カレー、丼、定食、ピザ、ハンバーガー、グラタン、ドリア、オムライス、クロックムッシュ、食事系プレート、モーニングセット
  - 食事なし = フルーツサンド、あんバターサンド、クリーム系サンド、ケーキ、パフェ、スイーツプレート、ケーキセット、ドリンクのみ、焼き菓子、パン販売のみ
- 迷う場合は「食事なし」

### 駐車場あり
- 既存タグに「駐車場」の記載がある場合のみ付与
- 台数は判定しないので「広い」とは書かない
=======
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
- トークン: patqS6soSoSI0MrYD（書き込み権限）

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
- PAT: patqS6soSoSI0MrYD

**Postiz**:
- API Key: pos_Nl5g1pOzJJgx6CuPHxMnVcZWVxsAhW2b
- Instagram 統合 ID: cmsopxrcz024opo0ygfgl0m4q
- BGM ビデオ URL: https://uploads.postiz.com/Dw9DWadyRH.mp4

**GitHub Actions**:
- ワークフロー: `.github/workflows/auto_instagram_post.yml`
- スクリプト: `scripts/auto_instagram_post.py`
- トリガー: 毎日 03:00 UTC（12:00 JST）、2 日経過で実行
>>>>>>> github/main
