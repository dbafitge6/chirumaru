import { getAllStores } from "@/lib/airtable";
import StoreBrowser from "@/components/StoreBrowser";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";

const GENRE_TAGS = [
  "カフェ",
  "パン屋・ベーカリー",
  "スイーツ・洋菓子店",
  "レストラン・食堂",
];

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let stores: Awaited<ReturnType<typeof getAllStores>> = [];
  let loadError: string | null = null;
  try {
    stores = await getAllStores();
  } catch (e) {
    loadError = e instanceof Error ? e.message : "不明なエラーが発生しました";
  }

  // エリア一覧を生成
  const areas = ["すべて", ...Array.from(new Set(stores.map((s) => s.area).filter(Boolean))).sort()];

  // タグ一覧を生成（最大15個）
  const tagSet = new Set<string>();
  stores.forEach((s) =>
    s.tags.forEach((t) => {
      if (!GENRE_TAGS.includes(t)) tagSet.add(t);
    })
  );
  const featureTags = Array.from(tagSet).sort().slice(0, 15);

  return (
    <>
      <SiteHeader />

      <main className="flex-1">
        <section className="relative overflow-hidden px-4 pb-10 pt-12 sm:px-6 sm:pt-16">
          {/* soft blob shapes, echoing rounded/kawaii mockup direction */}
          <div
            aria-hidden
            className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-blush/60 blur-2xl"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute -left-10 top-24 h-40 w-40 rounded-full bg-sand/70 blur-2xl"
          />
          <div className="relative mx-auto max-w-6xl">
            <p className="font-display text-sm font-bold tracking-wide text-terracotta">
              niigata cafe & bakery guide
            </p>
            <h1 className="mt-2 max-w-xl font-display text-3xl font-black leading-tight text-umber sm:text-4xl">
              今日のひと休み、
              <br />
              新潟のどこで過ごそう。
            </h1>
            <p className="mt-3 max-w-md text-sm text-umber/60">
              カフェ・パン屋・スイーツ店・喫茶店を、エリアやタグでゆるっと探せます。
            </p>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
          {loadError ? (
            <div className="rounded-3xl border border-dashed border-clay/30 bg-white/60 p-8 text-sm text-clay">
              お店の情報を読み込めませんでした。環境変数 AIRTABLE_API_KEY
              が正しく設定されているか確認してください。
            </div>
          ) : (
            <StoreBrowser areas={areas} featureTags={featureTags} />
          )}
        </section>
      </main>

      <SiteFooter />
    </>
  );
}
