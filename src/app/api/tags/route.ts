import { getAllStores } from "@/lib/airtable";

export async function GET() {
  try {
    const stores = await getAllStores();
    const menuCounts = new Map<string, number>();

    stores.forEach((store) => {
      if (Array.isArray(store.tags)) {
        store.tags.forEach((tag) => {
          if (tag && typeof tag === "string") {
            const parts = tag.split("/").map((p) => p.trim());

            // 2番目以降をメニュー・特徴タグとしてカウント（業態は除外）
            for (let i = 1; i < parts.length; i++) {
              if (parts[i]) {
                menuCounts.set(parts[i], (menuCounts.get(parts[i]) || 0) + 1);
              }
            }
          }
        });
      }
    });

    // 使用頻度が高い順にソートして、上位15タグを取得
    const menus = Array.from(menuCounts.entries())
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
