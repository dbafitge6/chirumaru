# ちるまる (chirumaru)

新潟のカフェ・パン屋・スイーツ店・喫茶店を探せるサイト。Next.js (App Router) + Airtable。

## セットアップ

```bash
npm install
cp .env.local.example .env.local
# .env.local を開いて AIRTABLE_API_KEY を設定する
npm run dev
```

`AIRTABLE_API_KEY` は Airtable の Personal Access Token です。
https://airtable.com/create/tokens で発行し、対象のベース(appyyoKM7RprQRht8)に対して
`data.records:read` スコープを付与してください。

## デプロイ (Vercel)

1. このリポジトリを GitHub に push
2. https://vercel.com で GitHub リポジトリを import
3. Vercelの環境変数に `AIRTABLE_API_KEY`(と必要なら `AIRTABLE_BASE_ID` / `AIRTABLE_TABLE_ID`)を設定
4. デプロイ後、chirumaru.jp の DNS を Vercel 側の指示に従って向ける
   (Xserverのドメイン設定 → chirumaru.jp → DNSレコード設定で A/CNAMEレコードを変更)

## 構成

- `src/lib/airtable.ts` — Airtable REST APIから店舗データを取得
- `src/components/StoreBrowser.tsx` — キーワード/エリア/タグでの絞り込みUI
- `src/components/StoreCard.tsx` — 一覧カード
- `src/app/store/[id]/page.tsx` — 店舗詳細ページ
