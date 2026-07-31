import { getAllStores } from "@/lib/airtable";

const GENRE_TAGS = new Set([
  "カフェ",
  "パン屋",
  "パン屋・ベーカリー",
  "ベーカリー",
  "スイーツ",
  "スイーツ・洋菓子店",
  "スイーツ・洋菓子",
  "洋菓子店",
  "和菓子",
  "和菓子店",
  "レストラン",
  "レストラン・食堂",
  "食堂",
  "喫茶店",
  "カフェ・喫茶",
]);

export async function GET() {
  try {
    const stores = await getAllStores();
    const tagCounts = new Map<string, number>();

    stores.forEach((store) => {
      if (Array.isArray(store.tags)) {
        store.tags.forEach((tag) => {
          if (tag && typeof tag === "string" && !GENRE_TAGS.has(tag)) {
            tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
          }
        });
      }
    });

    // 使用頻度が高い順にソートして、上位15タグを取得
    const menus = Array.from(tagCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15)
      .map(([tag]) => tag);

    return Response.json({ menus });
  } catch (error) {
    return Response.json(
      { error: "Failed to fetch tags" },
      { status: 500 }
    );
  }
}
