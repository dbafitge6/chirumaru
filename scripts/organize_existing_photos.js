/**
 * 既存 Airtable 写真を Googleドライブ に自動振り分け
 * 実行: node scripts/organize_existing_photos.js
 */

const Anthropic = require("@anthropic-ai/sdk");

// 設定
const AIRTABLE_TOKEN = process.env.AIRTABLE_TOKEN;
const AIRTABLE_BASE_ID = "appyyoKM7RprQRht8";
const AIRTABLE_TABLE_ID = "tblcOdcqCxzb7kX0e";
const DRIVE_FOLDER_ID = "1yGdyBXCX9934uP_IqMib48bWDzfoyPCb";
const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY || "";

if (!AIRTABLE_TOKEN) {
  console.error("❌ エラー: AIRTABLE_TOKEN 環境変数を設定してください");
  process.exit(1);
}

const client = new Anthropic.Anthropic({
  apiKey: CLAUDE_API_KEY,
});

async function getAllStores() {
  const stores = [];
  let offset = undefined;

  while (true) {
    const url = new URL(
      `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_TABLE_ID}`
    );
    if (offset) url.searchParams.append("offset", offset);

    const response = await fetch(url.toString(), {
      headers: { Authorization: `Bearer ${AIRTABLE_TOKEN}` },
    });

    const data = await response.json();
    stores.push(...data.records);

    if (!data.offset) break;
    offset = data.offset;
  }

  return stores;
}

async function analyzePhotoWithClaude(photoUrl) {
  try {
    const response = await client.messages.create({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 100,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "image",
              source: {
                type: "url",
                url: photoUrl,
              },
            },
            {
              type: "text",
              text: "この画像は、カフェ・飲食店の『外観』ですか、それとも『料理・メニュー』ですか？『外観』または『料理』のいずれか一つだけ答えてください。",
            },
          ],
        },
      ],
    });

    const category = response.content[0].text.trim();
    return category.includes("外観") ? "外観" : "料理";
  } catch (error) {
    console.error(`Claude API エラー (${photoUrl}):`, error.message);
    return "料理"; // デフォルト
  }
}

async function processStores() {
  const stores = await getAllStores();
  console.log(`${stores.length} 店舗を取得しました`);

  let processedCount = 0;
  let skippedCount = 0;

  for (const store of stores) {
    const storeName = store.fields.Name;
    const photoField = store.fields["写真/ロゴ"];

    if (!photoField) {
      skippedCount++;
      continue;
    }

    // 複数の URL が改行で区切られている場合を処理
    const photoUrls = photoField
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.startsWith("http"));

    if (photoUrls.length === 0) {
      skippedCount++;
      continue;
    }

    console.log(
      `\n📸 ${storeName} (${photoUrls.length} 枚の写真)`,
      "analyze..."
    );

    const results = [];

    for (const photoUrl of photoUrls) {
      const category = await analyzePhotoWithClaude(photoUrl);
      results.push({ url: photoUrl, category });
      console.log(
        `  ✓ ${category}: ${photoUrl.substring(0, 50)}...`
      );
    }

    // Airtable を更新（カテゴリ付きフォーマット）
    const updatedPhotoField = results
      .map((r) => `[${r.category}] ${r.url}`)
      .join("\n");

    await fetch(
      `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_TABLE_ID}/${store.id}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${AIRTABLE_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fields: {
            "写真/ロゴ": updatedPhotoField,
          },
        }),
      }
    );

    processedCount++;
    console.log(`  ✅ Airtable 更新完了`);
  }

  console.log(`\n\n📊 処理完了`);
  console.log(
    `  処理済み: ${processedCount} 店舗`
  );
  console.log(`  スキップ: ${skippedCount} 店舗`);
}

processStores().catch(console.error);
