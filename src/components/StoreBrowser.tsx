"use client";

import { useMemo, useState, useEffect, useRef } from "react";
import type { Store } from "@/lib/types";
import StoreCard from "./StoreCard";

const GENRE_TAGS = [
  "カフェ",
  "パン屋・ベーカリー",
  "スイーツ・洋菓子店",
  "レストラン・食堂",
];

export default function StoreBrowser({ stores }: { stores: Store[] }) {
  const [keyword, setKeyword] = useState("");
  const [area, setArea] = useState("すべて");
  const [activeTags, setActiveTags] = useState<string[]>([]);
  const [showFilter, setShowFilter] = useState(true);
  const scrollTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const handleScroll = () => {
      setShowFilter(false); // スクロール中は隠す

      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }

      scrollTimeout.current = setTimeout(() => {
        setShowFilter(true); // 1秒後に表示
      }, 1000);
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
    };
  }, []);

  const areas = useMemo(() => {
    const set = new Set(stores.map((s) => s.area).filter(Boolean));
    return ["すべて", ...Array.from(set).sort()];
  }, [stores]);

  const featureTags = useMemo(() => {
    const set = new Set<string>();
    stores.forEach((s) =>
      s.tags.forEach((t) => {
        if (!GENRE_TAGS.includes(t)) set.add(t);
      })
    );
    return Array.from(set).sort().slice(0, 15);
  }, [stores]);

  function toggleTag(tag: string) {
    setActiveTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  const filtered = useMemo(() => {
    const kw = keyword.trim().toLowerCase();
    return stores.filter((s) => {
      if (area !== "すべて" && s.area !== area) return false;
      if (activeTags.length > 0 && !activeTags.every((t) => s.tags.includes(t)))
        return false;
      if (kw) {
        const haystack = `${s.name} ${s.memo} ${s.menu} ${s.tags.join(" ")}`.toLowerCase();
        if (!haystack.includes(kw)) return false;
      }
      return true;
    });
  }, [stores, keyword, area, activeTags]);

  return (
    <div>
      {/* Filter bar */}
      <div
        className={`sticky top-0 z-20 -mx-4 mb-8 border-b border-umber/10 bg-cream/90 px-4 py-4 backdrop-blur-md sm:mx-0 sm:rounded-3xl sm:border sm:px-6 sm:shadow-sm transition-all duration-300 ${
          showFilter ? "" : "hidden"
        }`}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="お店の名前やメニューで探す"
              className="w-full rounded-full border border-umber/15 bg-white px-5 py-2.5 text-base text-umber placeholder:text-umber/40 focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/30"
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
        {filtered.length}件のお店が見つかりました
      </p>

      {filtered.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-umber/20 bg-white/50 py-16 text-center text-umber/50">
          条件に合うお店が見つかりませんでした。キーワードや絞り込みを変えてみてください。
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 pb-16 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((store) => (
            <StoreCard
              key={store.id}
              store={store}
              keyword={keyword}
              area={area}
              activeTags={activeTags}
            />
          ))}
        </div>
      )}
    </div>
  );
}
