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
