import { getAllStores } from "@/lib/airtable";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const keyword = searchParams.get("keyword") || "";
  const area = searchParams.get("area");
  const tagsParam = searchParams.get("tags");
  const offset = parseInt(searchParams.get("offset") || "0", 10);
  const limit = 20;

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

    // ページネーション
    const items = filtered.slice(offset, offset + limit);
    const hasMore = offset + limit < filtered.length;

    return Response.json({
      items,
      total: filtered.length,
      hasMore,
      offset,
    });
  } catch (error) {
    return Response.json(
      { error: "Failed to fetch stores" },
      { status: 500 }
    );
  }
}
