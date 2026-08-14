import { getAllStores } from "@/lib/airtable";
import { GENRE_TAGS, MAX_FEATURED_TAGS } from "@/lib/constants";

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

    // 2つ以上の店舗で使用されているタグのみを抽出（特定の店舗のメニュー項目は除外）
    const menus = Array.from(tagCounts.entries())
      .filter(([_, count]) => count >= 2)
      .sort((a, b) => b[1] - a[1])
      .slice(0, MAX_FEATURED_TAGS)
      .map(([tag]) => tag);

    return Response.json({ menus });
  } catch (error) {
    console.error("[/api/tags] Error:", error instanceof Error ? error.message : String(error));
    return Response.json(
      { error: "Failed to fetch tags" },
      { status: 500 }
    );
  }
}
