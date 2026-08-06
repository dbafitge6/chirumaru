import { getAllStores } from "@/lib/airtable";

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const keyword = searchParams.get("keyword") || "";
  const area = searchParams.get("area");
  const tagsParam = searchParams.get("tags");
  const shuffle = searchParams.get("shuffle") === "true";

  const tags = tagsParam ? tagsParam.split(",").filter(Boolean) : [];

  try {
    const stores = await getAllStores();

    // フィルタリング
    const kw = keyword.trim().toLowerCase();
    const filtered = stores.filter((s) => {
      if (area && area !== "すべて" && s.area !== area) return false;
      if (tags.length > 0 && !tags.every((t) => s.tags.includes(t))) return false;
      if (kw) {
        const haystack = `${s.name} ${s.memo} ${s.menu} ${s.tags.join(" ")}`.toLowerCase();
        if (!haystack.includes(kw)) return false;
      }
      return true;
    });

    // シャッフル（フィルターなし時）
    const items = shuffle ? shuffleArray(filtered) : filtered;

    return Response.json({
      items,
      total: items.length,
      hasMore: false,
    });
  } catch (error) {
    console.error("[API/stores] Error:", error);
    return Response.json(
      { error: "Failed to fetch stores", details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
