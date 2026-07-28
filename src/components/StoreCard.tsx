import Link from "next/link";
import type { Store } from "@/lib/types";
import { memo } from "react";

function StoreCard({
  store,
  keyword = "",
  area = "すべて",
  activeTags = [],
}: {
  store: Store;
  keyword?: string;
  area?: string;
  activeTags?: string[];
}) {
  const queryParams = new URLSearchParams();
  if (keyword) queryParams.set("keyword", keyword);
  if (area && area !== "すべて") queryParams.set("area", area);
  if (activeTags.length > 0) queryParams.set("tags", activeTags.join(","));
  const queryString = queryParams.toString();
  const href = `/store/${store.id}${queryString ? `?${queryString}` : ""}`;

  return (
    <Link
      href={href}
      className="group relative block overflow-hidden rounded-[28px] bg-white/80 shadow-[0_6px_20px_-8px_rgba(74,54,46,0.25)] ring-1 ring-umber/5 transition-transform duration-200 hover:-translate-y-1 hover:shadow-[0_14px_28px_-10px_rgba(193,95,66,0.35)]"
    >
      {/* signature: folded paper-bag corner, echoes the onigiri/paper-wrap motif */}
      <span
        aria-hidden
        className="absolute right-0 top-0 z-10 h-9 w-9 bg-cream"
        style={{ clipPath: "polygon(100% 0, 0 0, 100% 100%)" }}
      />
      <span
        aria-hidden
        className="absolute right-0 top-0 z-10 h-9 w-9 bg-blush shadow-[inset_2px_2px_4px_rgba(74,54,46,0.15)]"
        style={{ clipPath: "polygon(100% 0, 45% 0, 100% 55%)" }}
      />

      <div className="relative h-40 w-full overflow-hidden bg-gradient-to-br from-blush to-sand">
        {store.photoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={store.photoUrl}
            alt={store.name}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center font-display text-3xl text-terracotta/40">
            ちるまる
          </div>
        )}
        {store.area && (
          <span className="absolute bottom-2 left-2 rounded-full bg-umber/70 px-3 py-1 text-xs font-medium text-cream backdrop-blur-sm">
            {store.area}
          </span>
        )}
      </div>

      <div className="p-4">
        <h3 className="font-display text-lg font-bold leading-snug text-umber">
          {store.name}
        </h3>
        {store.memo && (
          <p className="mt-1 line-clamp-2 text-sm text-umber/70">{store.memo}</p>
        )}

        {store.tags.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-1.5">
            {store.tags.slice(0, 4).map((tag) => (
              <li
                key={tag}
                className="rounded-full bg-sand px-2.5 py-1 text-[11px] font-medium text-clay"
              >
                {tag}
              </li>
            ))}
          </ul>
        )}
      </div>
    </Link>
  );
}

export default memo(StoreCard);
