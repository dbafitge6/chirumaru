// ちるまる 写真投稿自動化スクリプト
// Google Forms → Google Drive フォルダ分け → Airtable 自動反映

const CONFIG = {
  PARENT_FOLDER_ID: '1jmOu2_sddS6uU0k-57c0BWz8aCx3ji_C',
  AIRTABLE_BASE_ID: 'appyyoKM7RprQRht8',
  AIRTABLE_TABLE_ID: 'tblcOdcqCxzb7kX0e',
  SHEET_ID: '1DwvZ2IRI126NXuitMS-kPsCZFVlp6VN5gDiJeXVMsQs',
};

// スプレッドシートカラムの定義
const COLUMNS = {
  TIMESTAMP: 0,      // タイムスタンプ
  STORE_NAME: 1,     // 店舗名
  PHOTO_URL: 2,      // お店の写真・メニュー写真をアップロード
  INSTAGRAM_ID: 3,   // お店名（インスタID等）
  COMMENT: 4,        // コメント・感想など
  PHOTO_TYPE: 5,     // 写真の種類（「外観」or「メニュー・商品」）
};

/**
 * Google Forms 新規回答時に自動実行
 * スプレッドシートのトリガーから呼び出される
 */
function onFormSubmit(e) {
  try {
    Logger.log('📝 新規フォーム回答を検出');

    const values = e.values;
    const timestamp = values[COLUMNS.TIMESTAMP];
    const storeName = values[COLUMNS.STORE_NAME];
    const photoUrl = values[COLUMNS.PHOTO_URL];
    const photoType = values[COLUMNS.PHOTO_TYPE];

    // バリデーション
    if (!storeName || !photoUrl || !photoType) {
      logResult('VALIDATION_ERROR', storeName, '店舗名、写真、または写真タイプがありません', null);
      return;
    }

    Logger.log(`📋 処理開始: ${storeName} | 写真: ${photoUrl} | タイプ: ${photoType}`);

    // ステップ1: Google Drive のサブフォルダを作成/確認
    const subFolderUrl = ensureSubFolder(storeName);
    if (!subFolderUrl) {
      logResult('FOLDER_ERROR', storeName, 'サブフォルダ作成失敗', null);
      return;
    }

    // ステップ2: 写真ファイルをサブフォルダに移動（ファイルURLを取得）
    const fileUrl = movePhotoToSubFolder(photoUrl, storeName);
    if (!fileUrl) {
      logResult('MOVE_ERROR', storeName, '写真移動失敗', subFolderUrl);
      return;
    }

    // ステップ3: Airtable に 写真ファイルのURL を反映（写真タイプ別に振り分け）
    const success = updateAirtablePhotos(storeName, fileUrl, photoType);
    if (!success) {
      logResult('AIRTABLE_ERROR', storeName, 'Airtable 更新失敗', subFolderUrl);
      return;
    }

    logResult('SUCCESS', storeName, `すべての処理が完了 [${photoType}]`, subFolderUrl);
    Logger.log('✅ 処理完了');

  } catch (error) {
    Logger.log('❌ エラー発生: ' + error.message);
    Logger.log(error.stack);
  }
}

/**
 * 店舗名のサブフォルダを作成（既存なら再利用）
 */
function ensureSubFolder(storeName) {
  try {
    const parentFolder = DriveApp.getFolderById(CONFIG.PARENT_FOLDER_ID);

    // 既存フォルダを検索
    const existing = parentFolder.getFoldersByName(storeName);
    if (existing.hasNext()) {
      const folder = existing.next();
      Logger.log(`✓ 既存フォルダを使用: ${storeName}`);
      return folder.getUrl();
    }

    // 新規フォルダを作成
    const newFolder = parentFolder.createFolder(storeName);
    Logger.log(`✓ 新しいフォルダを作成: ${storeName}`);
    return newFolder.getUrl();

  } catch (error) {
    Logger.log(`✗ フォルダ作成エラー (${storeName}): ${error.message}`);
    return null;
  }
}

/**
 * Google Drive の写真ファイルをサブフォルダに移動
 * 移動後のファイルの共有可能URL を返す
 */
function movePhotoToSubFolder(photoUrl, storeName) {
  try {
    // Google Drive の URL からファイル ID を抽出
    // フォーマット: https://drive.google.com/open?id=xxxxx
    const fileIdMatch = photoUrl.match(/id=([a-zA-Z0-9_-]+)/);
    if (!fileIdMatch) {
      Logger.log(`✗ ファイル ID を抽出できません: ${photoUrl}`);
      return null;
    }

    const fileId = fileIdMatch[1];
    const file = DriveApp.getFileById(fileId);
    const parentFolder = DriveApp.getFolderById(CONFIG.PARENT_FOLDER_ID);

    // 移動先フォルダを取得
    const destFolders = parentFolder.getFoldersByName(storeName);
    if (!destFolders.hasNext()) {
      Logger.log(`✗ 移動先フォルダが見つかりません: ${storeName}`);
      return null;
    }

    const destFolder = destFolders.next();

    // 既存親フォルダから移動
    const parents = file.getParents();
    while (parents.hasNext()) {
      const parent = parents.next();
      parent.removeFile(file);
    }

    // 新しい親フォルダに移動
    destFolder.addFile(file);

    // 写真ファイルを公開（共有可能リンク有効化）
    file.setSharing(DriveApp.Access.ANYONE, DriveApp.Permission.VIEW);

    // 共有可能な直接リンクを生成
    const fileUrl = `https://drive.google.com/uc?id=${fileId}&export=view`;

    Logger.log(`✓ 写真を移動完了: ${storeName}/${file.getName()}`);
    Logger.log(`✓ ファイルURL: ${fileUrl}`);
    return fileUrl;

  } catch (error) {
    Logger.log(`✗ 写真移動エラー (${storeName}): ${error.message}`);
    return null;
  }
}

/**
 * Airtable の店舗レコードに写真 URL を追加（写真タイプ別に振り分け）
 */
function updateAirtablePhotos(storeName, fileUrl, photoType) {
  try {
    const token = PropertiesService.getScriptProperties().getProperty('AIRTABLE_TOKEN');
    if (!token) {
      Logger.log('✗ AIRTABLE_TOKEN が設定されていません');
      return false;
    }

    // Airtable API で店舗を検索
    const searchUrl = `https://api.airtable.com/v0/${CONFIG.AIRTABLE_BASE_ID}/${CONFIG.AIRTABLE_TABLE_ID}`;
    const params = {
      method: 'get',
      headers: { 'Authorization': `Bearer ${token}` },
      muteHttpExceptions: true,
    };

    const response = UrlFetchApp.fetch(searchUrl + `?filterByFormula=FIND("${storeName}",{Store Name})>0`, params);
    const data = JSON.parse(response.getContentText());

    if (!data.records || data.records.length === 0) {
      Logger.log(`✗ Airtable で店舗が見つかりません: ${storeName}`);
      return false;
    }

    const record = data.records[0];
    const recordId = record.id;

    // 写真タイプに応じて、更新対象フィールドと既存値を取得
    let fieldName, existing;
    if (photoType === '外観') {
      fieldName = '外観写真';
      existing = record.fields['外観写真'] || '';
    } else if (photoType === 'メニュー・商品') {
      fieldName = 'メニュー写真';
      existing = record.fields['メニュー写真'] || '';
    } else {
      Logger.log(`✗ 不正な写真タイプです: ${photoType}`);
      return false;
    }

    // 既存値に新しい URL を追記（改行区切り）
    const updated = existing ? `${existing}\n${fileUrl}` : fileUrl;

    // Airtable を更新
    const updateUrl = `${searchUrl}/${recordId}`;
    const updateParams = {
      method: 'patch',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      payload: JSON.stringify({
        fields: { [fieldName]: updated }
      }),
      muteHttpExceptions: true,
    };

    const updateResponse = UrlFetchApp.fetch(updateUrl, updateParams);
    if (updateResponse.getResponseCode() !== 200) {
      Logger.log(`✗ Airtable 更新失敗 (${recordId}): ${updateResponse.getContentText()}`);
      return false;
    }

    Logger.log(`✓ Airtable 更新完了: ${storeName} (${fieldName})`);
    return true;

  } catch (error) {
    Logger.log(`✗ Airtable 更新エラー (${storeName}): ${error.message}`);
    return false;
  }
}

/**
 * 処理ログを Google Sheet に記録
 */
function logResult(status, storeName, message, folderUrl) {
  try {
    const sheet = SpreadsheetApp.openById(CONFIG.SHEET_ID).getSheetByName('処理ログ') ||
                  SpreadsheetApp.openById(CONFIG.SHEET_ID).insertSheet('処理ログ');

    // ヘッダー行を追加（初回のみ）
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['タイムスタンプ', 'ステータス', '店舗名', 'メッセージ', 'フォルダURL']);
    }

    sheet.appendRow([
      new Date(),
      status,
      storeName,
      message,
      folderUrl || ''
    ]);

  } catch (error) {
    Logger.log(`⚠️ ログ記録エラー: ${error.message}`);
  }
}

/**
 * Airtable トークンをスクリプト プロパティに設定
 * 実行方法: スクリプト エディタで setAirtableToken() を実行
 */
function setAirtableToken() {
  const token = 'ここにAirtable PATを貼り付け'; // 環境変数または GitHub Secrets から取得
  PropertiesService.getScriptProperties().setProperty('AIRTABLE_TOKEN', token);
  Logger.log('✓ AIRTABLE_TOKEN を設定しました');
}

/**
 * テスト実行用（デバッグ用）
 */
function testPhotoAutomation() {
  // テスト用の仮データ
  const testEvent = {
    values: [
      new Date(),
      'テスト店舗',
      'https://drive.google.com/open?id=TEST_FILE_ID',
      '@test_instagram',
      'テストコメント'
    ]
  };

  Logger.log('🧪 テスト実行中...');
  onFormSubmit(testEvent);
}
