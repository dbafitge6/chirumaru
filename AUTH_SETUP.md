# Authentication Setup Guide

chirumaru 認証機能のセットアップガイド

## 実装済み機能

### 1. メール/パスワード認証
- ユーザー登録（サインアップ）
- ユーザーログイン
- パスワードハッシング（bcryptjs）

### 2. ユーザーデータ管理
- Airtable Users テーブルへの自動保存
- ローカルストレージによるセッション管理
- ログイン状態の永続化

### 3. UI コンポーネント
- ログインページ (`/login`)
- ログイン/アカウント作成フォーム切り替え
- ナビゲーションバーのログイン/ログアウトボタン
- ユーザーメール表示

## セットアップ手順

### Step 1: Airtable API キー取得

1. https://airtable.com/create/tokens にアクセス
2. 新しい Personal Access Token を作成
3. 以下のスコープを許可：
   - `data.records:read` - レコード読み取り
   - `data.records:write` - レコード書き込み
4. ベース（chirumaru）へのアクセスを許可

### Step 2: 環境変数設定

`.env.local` ファイルを編集：

```env
AIRTABLE_BASE_ID=appyyoKM7RprQRht8
AIRTABLE_API_KEY=pat_YOUR_TOKEN_HERE
```

`pat_YOUR_TOKEN_HERE` を Step 1 で取得したトークンに置き換えてください。

### Step 3: 開発サーバー再起動

```bash
npm run dev
```

## 使用方法

### ユーザー登録
1. ホームページの「ログイン」ボタンをクリック
2. 「アカウント作成はこちら」を選択
3. メールアドレスとパスワードを入力
4. 「作成」をクリック

### ログイン
1. `/login` ページにアクセス
2. メールアドレスとパスワードを入力
3. 「ログイン」をクリック

### ログアウト
ナビゲーションバーの「ログアウト」ボタンをクリック

## API エンドポイント

### POST /api/auth/signup
ユーザー登録

```bash
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "loginMethod": "Email"
  }'
```

### POST /api/auth/login
ユーザーログイン

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

## ファイル構成

```
src/
  ├── app/
  │   ├── login/page.tsx          # ログインページ
  │   └── api/auth/
  │       ├── signup/route.ts     # サインアップ API
  │       └── login/route.ts      # ログイン API
  ├── components/
  │   ├── LoginForm.tsx           # ログインフォーム（切り替え機能）
  │   └── SiteHeader.tsx          # ナビゲーション（ログイン状態表示）
  └── lib/
      └── auth.ts                 # 認証ロジック（bcrypt）

.env.local                         # 環境変数（要設定）
```

## セキュリティ考慮事項

- パスワードは bcryptjs（10ラウンド）でハッシング
- API キーは `.env.local` に保存（`.gitignore` で無視）
- ローカルストレージはセッション情報のみ（パスワード非保存）
- 本番環境では HTTPS を使用必須

## 次のステップ（オプション）

- [ ] Google OAuth の統合
- [ ] パスワードリセット機能
- [ ] メール確認機能
- [ ] 2FA（二要素認証）
- [ ] ユーザープロフィールページ
