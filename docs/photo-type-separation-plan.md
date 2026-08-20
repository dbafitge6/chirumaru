# 写真投稿仕組み改修計画

## 概要
投稿された写真を「外観写真」と「メニュー・商品写真」に分類し、異なるフィールドに保存・表示する

---

## 1. Google Forms 修正

### フォーム URL
https://docs.google.com/forms/d/1FAIpQLSdnUJREkYKXAg50FVopvcFer6OxtRG41dTSL7RDaHy34yoDfQ

### 追加する質問
- **質問文**: 「写真の種類を選んでください」
- **質問タイプ**: ラジオボタン（単一選択）
- **選択肢**:
  - 「外観」
  - 「メニュー・商品」
- **必須**: はい
- **エントリー ID**: `entry.XXXXX`（Google Forms で自動割り当て、確認後に記録）

### スプレッドシート側への影響
フォーム回答スプレッドシートに新しいカラムが自動追加される

---

## 2. Airtable フィールド追加

### 追加するフィールド

| フィールド名 | 型 | 説明 | 保存形式 |
|---|---|---|---|
| **外観写真** | Long text | 店舗の外観・店内 | 改行区切りURL（複数件、蓄積） |
| **メニュー写真** | Long text | メニュー・商品 | 改行区切りURL（複数件、蓄積） |

### 既存フィールドの取扱い
**案1：Photos/Logo は廃止**
- 新しいシステムでは「外観写真」「メニュー写真」のみを使用
- 移行段階では、既存の Photos/Logo の内容を適切に振り分けて、新フィールドに移動

**案2：Photos/Logo は保持（互換性維持）**
- Photos/Logo を「外観写真」のバックアップとして保持
- 新しい投稿は「外観写真」「メニュー写真」を使用

**推奨**: **案1（廃止）** - シンプルで管理しやすい

---

## 3. Apps Script 修正（scripts/photo_submission_automation.gs）

### 新しい列定義
```javascript
const COLUMNS = {
  TIMESTAMP: 0,      // タイムスタンプ
  STORE_NAME: 1,     // 店舗名
  PHOTO_URL: 2,      // お店の写真・メニュー写真をアップロード
  INSTAGRAM_ID: 3,   // お店名（インスタID等）
  COMMENT: 4,        // コメント・感想など
  PHOTO_TYPE: 5,     // ← 新規追加：「外観」or「メニュー・商品」
};
```

### onFormSubmit() の修正フロー
```
1. フォーム回答を読み込む
2. 店舗名、写真URL、写真タイプを抽出
3. 写真ファイルを Google Drive にアップロード（既存）
4. 写真タイプに応じて Airtable を更新：
   ├─ 「外観」→ 「外観写真」フィールドに上書き（1件）
   └─ 「メニュー・商品」→ 「メニュー写真」フィールドに追記（改行区切り）
5. 処理ログに記録
```

### 修正内容
```javascript
// 新しい updateAirtablePhotos 関数のシグネチャ
updateAirtablePhotos(storeName, fileUrl, photoType)

// 内部ロジック（両フィールド共に蓄積）
if (photoType === "外観") {
  // 「外観写真」フィールドに追記（既存値を保持、改行で蓄積）
  GET 既存値
  PATCH fields: { "外観写真": 既存値 ? 既存値 + "\n" + fileUrl : fileUrl }
} else if (photoType === "メニュー・商品") {
  // 「メニュー写真」フィールドに追記（既存値を保持、改行で蓄積）
  GET 既存値
  PATCH fields: { "メニュー写真": 既存値 ? 既存値 + "\n" + fileUrl : fileUrl }
}
```

---

## 4. フロントエンド修正（店舗詳細ページ）

### 変更対象
`src/app/store/[id]/page.tsx`

### Store 型の修正（lib/types.ts）
```typescript
type Store = {
  // ... 既存フィールド ...
  photoUrl: string;        // ← そのまま（外観写真から取得）
  exteriorPhotoUrl: string; // ← 新規：外観写真
  menuPhotoUrls: string[];  // ← 新規：メニュー写真配列
}
```

### airtable.ts の toStore() 修正
```javascript
function toStore(record): Store {
  return {
    // ... 既存 ...
    photoUrl: splitPhotoUrls(f["外観写真"])[0] ?? "",
    exteriorPhotoUrl: f["外観写真"] ?? "",
    menuPhotoUrls: splitPhotoUrls(f["メニュー写真"]),
  };
}
```

### 店舗詳細ページのレイアウト変更

#### 現在のレイアウト
```
┌─ ナビゲーション（前へ/一覧/次へ）
├─ メイン画像（photoUrl）
├─ 店名、住所、営業時間等
├─ 「写真を投稿」ボタン
├─ Google Map 埋め込み
└─ 住所、電話番号等
```

#### 修正後のレイアウト（推奨：別々に表示）
```
┌─ ナビゲーション（前へ/一覧/次へ）
├─ メイン画像（外観写真の1枚目）
├─ 店名、住所、営業時間等
├─ 「写真を投稿」ボタン
├─ 📸 外観写真ギャラリーセクション（2枚目以降）（新規）
│  ├─ 見出し：「店舗の様子」
│  └─ 複数枚のスクロール表示（あれば）
├─ 📸 メニュー・商品写真ギャラリーセクション（新規）
│  ├─ 見出し：「メニュー・商品」
│  └─ 複数枚のスクロール表示（あれば）
├─ Google Map 埋め込み
└─ 住所、電話番号等
```

**理由：別々に表示する方が、ユーザーにとって写真の種類が明確になり、見やすい**

### コンポーネント側の修正
- PhotoScroll コンポーネントを既存のように再利用
- メニュー写真用に別セクションを追加

---

## 5. 既存データの移行

### 対象レコード
- ナミテテ
- HARUMACHI coffee
- COFFEE STAND
- その他、Photos/Logo フィールドに値が入っているすべての店舗

### 移行戦略

| 店舗 | 現在の写真内容 | 移行先 | 理由 |
|---|---|---|---|
| ナミテテ | 商品（スイーツ） | 「メニュー写真」 | 商品写真 |
| HARUMACHI coffee | メニュー看板？ | 「メニュー写真」 | メニュー関連 |
| COFFEE STAND | フォルダURL（要確認） | 「外観写真」 | デフォルト |

### 移行方法

**オプション1：Airtable UI で手動移行**
- Admin ページから確認して手動で振り分け

**オプション2：スクリプトで自動移行**
```javascript
// update_photo_fields_migration.gs
// Photos/Logo → 「外観写真」へ一括コピー（初期移行）
```

### 推奨
**オプション1**（手動）- 数件なので確実

---

## 実装順序

1. ✅ **準備**：Google Forms で新質問を追加
2. ✅ **Airtable**：新フィールド「外観写真」「メニュー写真」を追加
3. ✅ **Apps Script**：updateAirtablePhotos() を修正
4. ✅ **フロントエンド**：Store 型、toStore()、ページレイアウトを修正
5. ✅ **データ移行**：既存データを新フィールドに移動
6. ✅ **テスト**：新フォーム → Airtable → 表示 の一連フロー確認

---

## チェックリスト

- [ ] Google Forms に質問追加、エントリー ID を記録
- [ ] Airtable に新フィールド追加（「外観写真」「メニュー写真」）
- [ ] Apps Script 修正・デプロイ
- [ ] 型定義・airtable.ts 修正
- [ ] 店舗詳細ページレイアウト修正
- [ ] 既存データ移行（手動確認）
- [ ] 全体テスト（新規投稿から表示確認）
