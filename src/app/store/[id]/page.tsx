import Link from "next/link";
import { notFound } from "next/navigation";
import { getStoreWithNeighbors } from "@/lib/airtable";
import SiteHeader from "@/components/SiteHeader";
import PhotoScroll from "@/components/PhotoScroll";

export const dynamic = "force-dynamic";

export default async function StorePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { id } = await params;
  const query = await searchParams;

  // Extract filter parameters from URL query string
  const keyword = typeof query.keyword === "string" ? query.keyword : undefined;
  const area = typeof query.area === "string" ? query.area : undefined;
  const tagsParam = typeof query.tags === "string" ? query.tags : undefined;
  const tags = tagsParam ? tagsParam.split(",").filter(Boolean) : undefined;

  const result = await getStoreWithNeighbors(id, {
    keyword,
    area: area && area !== "すべて" ? area : undefined,
    tags,
  }).catch(() => null);
  if (!result) notFound();
  const { store, prevId, nextId } = result;

  const mapQuery =
    (store.mapUrl && store.mapUrl.trim()) ||
    [store.name, store.address].filter(Boolean).join(" ");
  const mapSearchUrl = mapQuery
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapQuery)}`
    : null;
  const mapEmbedUrl = mapQuery
    ? `https://www.google.com/maps?q=${encodeURIComponent(mapQuery)}&output=embed`
    : null;
  const photoSubmitUrl = `https://docs.google.com/forms/d/e/1FAIpQLSdnUJREkYKXAg50FVopvcFer6OxtRG41dTSL7RDaHy34yoDfQ/viewform?usp=pp_url&entry.1442856618=${encodeURIComponent(store.name)}`;

  return (
    <>
      <SiteHeader />

      <main className="flex-1">
        <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
          <div className="flex items-center justify-between gap-2">
            {prevId ? (
              <Link
                href={`/store/${prevId}?keyword=${encodeURIComponent(keyword || "")}&area=${encodeURIComponent(area || "")}&tags=${encodeURIComponent(tags?.join(",") || "")}`}
                className="inline-flex items-center gap-1 rounded-full border border-umber/15 bg-white px-4 py-2 text-sm font-medium text-umber hover:border-terracotta/50 hover:text-clay"
              >
                ← 前へ
              </Link>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full border border-umber/10 bg-white/50 px-4 py-2 text-sm font-medium text-umber/30">
                ← 前へ
              </span>
            )}

            <Link
              href="/"
              className="text-sm text-terracotta hover:text-clay"
            >
              一覧にもどる
            </Link>

            {nextId ? (
              <Link
                href={`/store/${nextId}?keyword=${encodeURIComponent(keyword || "")}&area=${encodeURIComponent(area || "")}&tags=${encodeURIComponent(tags?.join(",") || "")}`}
                className="inline-flex items-center gap-1 rounded-full border border-umber/15 bg-white px-4 py-2 text-sm font-medium text-umber hover:border-terracotta/50 hover:text-clay"
              >
                次へ →
              </Link>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full border border-umber/10 bg-white/50 px-4 py-2 text-sm font-medium text-umber/30">
                次へ →
              </span>
            )}
          </div>

          <div className="mt-4 overflow-hidden rounded-[28px] bg-white/80 shadow-[0_6px_20px_-8px_rgba(74,54,46,0.25)]">
            <div className="h-56 w-full bg-gradient-to-br from-blush to-sand">
              {store.photoUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={store.photoUrl}
                  alt={store.name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center font-display text-4xl text-terracotta/40">
                  ちるまる
                </div>
              )}
            </div>

            <div className="p-6 sm:p-8">
              {store.area && (
                <span className="rounded-full bg-sand px-3 py-1 text-xs font-medium text-clay">
                  {store.area}
                </span>
              )}
              <h1 className="mt-3 font-display text-2xl font-bold text-umber sm:text-3xl">
                {store.name}
              </h1>

              {store.tags.length > 0 && (
                <ul className="mt-3 flex flex-wrap gap-1.5">
                  {store.tags.map((tag) => (
                    <li
                      key={tag}
                      className="rounded-full bg-blush px-2.5 py-1 text-[11px] font-medium text-clay"
                    >
                      {tag}
                    </li>
                  ))}
                </ul>
              )}

              {store.memo && (
                <p className="mt-5 text-sm leading-relaxed text-umber/80">
                  {store.memo}
                </p>
              )}

              <PhotoScroll photos={store.photoUrls} storeName={store.name} />

              <dl className="mt-6 space-y-3 border-t border-umber/10 pt-6 text-sm">
                {store.address && (
                  <div className="flex gap-3">
                    <dt className="w-20 shrink-0 text-umber/50">住所</dt>
                    <dd className="text-umber">{store.address}</dd>
                  </div>
                )}
                {store.hours && (
                  <div className="flex gap-3">
                    <dt className="w-20 shrink-0 text-umber/50">営業時間</dt>
                    <dd className="text-umber">{store.hours}</dd>
                  </div>
                )}
                {store.phone && (
                  <div className="flex gap-3">
                    <dt className="w-20 shrink-0 text-umber/50">電話番号</dt>
                    <dd className="text-umber">{store.phone}</dd>
                  </div>
                )}
                {store.menu && (
                  <div className="flex gap-3">
                    <dt className="w-20 shrink-0 text-umber/50">メニュー</dt>
                    <dd className="whitespace-pre-line text-umber">
                      {store.menu}
                    </dd>
                  </div>
                )}
              </dl>

              <div className="mt-6 flex flex-col gap-2 sm:flex-wrap sm:gap-3">
                {mapSearchUrl && (
                  <a
                    href={mapSearchUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full border border-terracotta/40 bg-cream px-5 py-2.5 text-sm font-medium text-clay hover:bg-blush/40 transition-colors text-center"
                  >
                    Googleマップで開く
                  </a>
                )}
                {store.website && (
                  <a
                    href={store.website}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full border border-umber/15 bg-white px-5 py-2.5 text-sm font-medium text-umber hover:border-terracotta/50 text-center"
                  >
                    公式サイト
                  </a>
                )}

                <a
                  href={photoSubmitUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full border border-terracotta/40 bg-cream px-5 py-2.5 text-sm font-medium text-clay hover:bg-blush/40 transition-colors text-center"
                >
                  📷 写真を投稿する
                </a>
              </div>

              {mapEmbedUrl && (
                <div className="mt-6 overflow-hidden rounded-2xl border border-umber/10">
                  <iframe
                    src={mapEmbedUrl}
                    width="100%"
                    height="280"
                    style={{ border: 0 }}
                    loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade"
                    title={`${store.name}の地図`}
                  />
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between gap-2">
            {prevId ? (
              <Link
                href={`/store/${prevId}`}
                className="inline-flex items-center gap-1 rounded-full border border-umber/15 bg-white px-4 py-2 text-sm font-medium text-umber hover:border-terracotta/50 hover:text-clay"
              >
                ← 前へ
              </Link>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full border border-umber/10 bg-white/50 px-4 py-2 text-sm font-medium text-umber/30">
                ← 前へ
              </span>
            )}

            <Link
              href="/"
              className="text-sm text-terracotta hover:text-clay"
            >
              一覧にもどる
            </Link>

            {nextId ? (
              <Link
                href={`/store/${nextId}`}
                className="inline-flex items-center gap-1 rounded-full border border-umber/15 bg-white px-4 py-2 text-sm font-medium text-umber hover:border-terracotta/50 hover:text-clay"
              >
                次へ →
              </Link>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full border border-umber/10 bg-white/50 px-4 py-2 text-sm font-medium text-umber/30">
                次へ →
              </span>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
