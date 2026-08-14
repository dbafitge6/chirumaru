@AGENTS.md

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
