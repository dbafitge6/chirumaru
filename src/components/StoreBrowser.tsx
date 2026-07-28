"use client";

import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import type { Store } from "@/lib/types";
import StoreCard from "./StoreCard";

const GENRE_TAGS = [
  "カフェ",
  "パン屋・ベーカリー",
  "スイーツ・洋菓子店",
  "レストラン・食堂",
];

export default function StoreBrowser({
  areas,
  featureTags,
}: {
  areas: string[];
  featureTags: string[];
}) {
  const [keyword, setKeyword] = useState("");
  const [area, setArea] = useState("すべて");
  const [activeTags, setActiveTags] = useState<string[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
    debounceTimeout.current = setTimeout(() => {
      loadStores(0);
    }, keyword ? 300 : 0);
  }, [keyword, area, activeTags, loadStores]);


  const loadStores = useCallback(async (offset: number) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (keyword) params.set("keyword", keyword);
      if (area && area !== "すべて") params.set("area", area);
      if (activeTags.length > 0) params.set("tags", activeTags.join(","));
      params.set("offset", offset.toString());

      const res = await fetch(`/api/stores?${params}`);
      const data = await res.json();

      if (offset === 0) {
        setStores(data.items);
      } else {
        setStores((prev) => [...prev, ...data.items]);
      }
      setTotal(data.total);
      setHasMore(data.hasMore);
    } catch (error) {
      console.error("Failed to load stores:", error);
    } finally {
      setLoading(false);
    }
  }, [keyword, area, activeTags]);

  function toggleTag(tag: string) {
    setActiveTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  return (
    <div>
      <div className="sticky top-0 z-20 -mx-4 mb-8 border-b border-umber/10 bg-cream/90 px-4 py-4 backdrop-blur-md sm:mx-0 sm:rounded-3xl sm:border sm:px-6 sm:shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="お店の名前やメニューで探す"
              className="w-full rounded-full border border-umber/15 bg-white px-5 py-2.5 text-base text-umber placeholder:text-umber/40 focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/30"
              style={{ WebkitAppearance: "none", appearance: "none" }}
            />
          </div>
          <select
            value={area}
            onChange={(e) => setArea(e.target.value)}
            className="rounded-full border border-umber/15 bg-white px-4 py-2.5 text-sm text-umber focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/30 sm:w-48"
          >
            {areas.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {featureTags.map((tag) => {
            const active = activeTags.includes(tag);
            return (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                  active
                    ? "border-terracotta bg-terracotta text-white"
                    : "border-umber/15 bg-white text-umber/70 hover:border-terracotta/50 hover:text-clay"
                }`}
              >
                {tag}
              </button>
            );
          })}
        </div>
      </div>

      <p className="mb-4 px-1 text-sm text-umber/60">
        {total}件のお店が見つかりました
      </p>

      {total === 0 ? (
        <div className="rounded-3xl border border-dashed border-umber/20 bg-white/50 py-16 text-center text-umber/50">
          条件に合うお店が見つかりませんでした。キーワードや絞り込みを変えてみてください。
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-5 pb-16 sm:grid-cols-2 lg:grid-cols-3">
            {stores.map((store) => (
              <StoreCard
                key={store.id}
                store={store}
                keyword={keyword}
                area={area}
                activeTags={activeTags}
              />
            ))}
          </div>

          {hasMore && (
            <div className="text-center pb-16">
              <button
                onClick={() => loadStores(stores.length)}
                disabled={loading}
                className="rounded-full bg-terracotta px-6 py-2.5 text-sm font-medium text-white hover:bg-clay disabled:opacity-50"
              >
                {loading ? "読み込み中..." : "もっと見る"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
