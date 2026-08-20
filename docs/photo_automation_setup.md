# 写真投稿自動化セットアップガイド

Google Forms の写真投稿を自動化して、Google Drive のフォルダ分け → Airtable 反映まで自動処理します。

## セットアップ手順

### 1. Google Sheets で Apps Script エディタを開く

スプレッドシート: https://docs.google.com/spreadsheets/d/1DwvZ2IRI126NXuitMS-kPsCZFVlp6VN5gDiJeXVMsQs

1. **ツール** → **Apps Script** をクリック
2. 新しいタブで Apps Script エディタが開きます

### 2. スクリプトをコピー&ペースト

`scripts/photo_submission_automation.gs` の内容をコピーして、Apps Script エディタに貼り付けます。

**注意**: 既存のコードがある場合は、すべて削除してから貼り付けてください。

### 3. Airtable トークンを設定

Apps Script エディタで以下を実行：

1. エディタで `setAirtableToken()` 関数を選択
2. **実行** ボタンをクリック（▶️）
3. 権限承認ダイアログが表示されます → **許可** をクリック

**または、以下の手順で手動設定：**

```javascript
// スクリプト プロパティに直接設定
PropertiesService.getScriptProperties().setProperty('AIRTABLE_TOKEN', 'pat_xxx');
```

Airtable のトークンは GitHub Secrets `AIRTABLE_TOKEN` を使用します。

### 4. トリガーを設定

Google Forms の新規回答時に自動実行するようにトリガーを設定します：

1. Apps Script エディタで **トリガー** 左パネル（時計アイコン）をクリック
2. **トリガーを作成** をクリック
3. 以下を設定：
   - **実行する関数**: `onFormSubmit`
   - **イベントの種類**: `フォーム送信時`
   - **デプロイ**: `Head`

4. **保存** をクリック

### 5. テスト実行

実装前にテストを実行：

1. Apps Script エディタで `testPhotoAutomation()` 関数を選択
2. **実行** ボタンをクリック
3. ログを確認（**実行ログ** で詳細を確認）

## 動作フロー

```
Google Forms 新規回答
    ↓
onFormSubmit トリガー実行
    ↓
1️⃣ 店舗名のサブフォルダを確認/作成
   （親フォルダ内に店舗名でフォルダ作成）
    ↓
2️⃣ 写真ファイルをサブフォルダに移動
   （フォーム回答の Google Drive ファイル ID から取得）
    ↓
3️⃣ Airtable の該当店舗に フォルダ URL を追加
   （Photos/Logo フィールドに追加）
    ↓
4️⃣ 処理ログをスプレッドシートに記録
   （「処理ログ」シートに自動作成）
    ↓
✅ 完了
```

## スプレッドシート構成

### フォーム回答シート（自動作成）
- **カラム A**: タイムスタンプ
- **カラム B**: 店舗名（重要）
- **カラム C**: お店の写真・メニュー写真をアップロード（Google Drive URL）
- **カラム D**: お店名（インスタID等）
- **カラム E**: コメント・感想など

### 処理ログシート（自動作成）
- **タイムスタンプ**: 処理実行時刻
- **ステータス**: SUCCESS / ERROR / VALIDATION_ERROR など
- **店舗名**: 処理対象の店舗
- **メッセージ**: 処理結果のメッセージ
- **フォルダURL**: 作成/使用したフォルダへのリンク

## トラブルシューティング

### エラー: "AIRTABLE_TOKEN が設定されていません"
→ `setAirtableToken()` を実行して token を設定してください

### エラー: "ファイル ID を抽出できません"
→ Google Drive URL の形式を確認してください
- 正しい形式: `https://drive.google.com/open?id=xxxxx`

### エラー: "Airtable で店舗が見つかりません"
→ Airtable の店舗名とフォーム回答の店舗名が一致しているか確認してください

### トリガーが実行されない
→ 以下を確認：
1. Apps Script にトリガーが設定されているか
2. Airtable トークンが正しく設定されているか
3. Google Forms が正しくスプレッドシートに連携しているか

## ログの確認

### リアルタイムログ
Apps Script エディタの **実行ログ** で最新の処理結果を確認：
1. **実行ログ** ボタンをクリック
2. 最新の実行結果を確認

### 処理ログシート
スプレッドシートの **「処理ログ」** シートで全処理履歴を確認：
- STATUS が `SUCCESS` → 処理完了
- STATUS が `ERROR` → 処理失敗（メッセージを確認）

## 注意事項

- **フォルダ ID が重要**: CONFIG.PARENT_FOLDER_ID を正しく設定してください
- **Airtable 店舗名**: フォーム回答の「店舗名」と Airtable の「Store Name」が一致する必要があります
- **写真の自動検出**: Google Drive の URL から自動で写真を検出します
- **複数写真**: 1つの回答に複数の写真が含まれる場合、最初の写真が処理されます

## 今後の拡張

- [ ] 複数写真の対応
- [ ] 写真の自動リサイズ
- [ ] LINE 通知
- [ ] Slack 通知
- [ ] 不正検出（スパム フィルタ）
