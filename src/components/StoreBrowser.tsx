"use client";

import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import type { Store } from "@/lib/types";
import StoreCard from "./StoreCard";
import { getGeolocation, calculateDistance } from "@/lib/geolocation";

// ローディング中に出す新潟カフェ豆知識。
// 「読み込み中...」だけの無機質な待機時間を、少しでも発見のきっかけに変える。
const TRIVIA = [
  "新潟は蔵元の数が全国最多。日本酒を使ったスイーツを出すカフェも。",
  "自家焙煎の豆は、見た目より“香りの違い”に注目すると個性がわかりやすい。",
  "古民家カフェは、梁や土壁が残っている店ほど築100年を超えていることも。",
  "コーヒーの好みは、酸味・甘み・余韻の3点で言語化すると見つけやすい。",
  "新潟市の砂丘地エリアには、地図に載りにくい一軒家カフェが点在しています。",
  "焼き菓子は開店直後の“1回目の焼き上がり”が一番香ばしいと言われます。",
];

export default function StoreBrowser({
  areas,
  featureTags,
  discoveryTags = [],
}: {
  areas: string[];
  featureTags: string[];
  discoveryTags?: string[];
}) {
  const [keyword, setKeyword] = useState("");
  const [area, setArea] = useState("すべて");
  const [activeTags, setActiveTags] = useState<string[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showFilter, setShowFilter] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [menus, setMenus] = useState<string[]>([]);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [useNearby, setUseNearby] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [trivia, setTrivia] = useState(TRIVIA[0]);
  const distanceMap = useMemo(() => {
    if (!useNearby || !userLocation) return {};
    const map: Record<string, number> = {};
    stores.forEach(store => {
      if (store.latitude && store.longitude) {
        map[store.id] = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          store.latitude,
          store.longitude
        );
      }
    });
    return map;
  }, [useNearby, userLocation, stores]);

  const debounceTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setMounted(true);
    const saved = JSON.parse(localStorage.getItem('favorites') || '[]');
    setFavorites(saved);

    const savedFilters = JSON.parse(localStorage.getItem('storeFilters') || '{}');
    if (savedFilters.keyword) setKeyword(savedFilters.keyword);
    if (savedFilters.area) setArea(savedFilters.area);
    if (savedFilters.activeTags) setActiveTags(savedFilters.activeTags);
  }, []);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const res = await fetch("/api/tags");
        const data = await res.json();
        setMenus(data.menus || []);
      } catch (error) {
        console.error("Failed to fetch tags:", error);
        setMenus([]);
      }
    };
    fetchTags();
  }, []);

  const loadStores = useCallback(async (offset: number) => {
    setLoading(true);
    if (offset === 0) {
      setTrivia(TRIVIA[Math.floor(Math.random() * TRIVIA.length)]);
    }
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

  useEffect(() => {
    if (mounted) {
      localStorage.setItem('storeFilters', JSON.stringify({
        keyword,
        area,
        activeTags,
      }));
    }
  }, [keyword, area, activeTags, mounted]);

  useEffect(() => {
    if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
    debounceTimeout.current = setTimeout(() => {
      loadStores(0);
    }, keyword ? 300 : 0);
    return () => {
      if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
    };
  }, [keyword, area, activeTags, loadStores]);

  function toggleTag(tag: string) {
    setActiveTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  function clearAllFilters() {
    setKeyword("");
    setArea("すべて");
    setActiveTags([]);
    localStorage.removeItem('storeFilters');
  }

  async function handleRequestLocation() {
    setLocationError(null);
    try {
      const coords = await getGeolocation();
      setUserLocation({ lat: coords.latitude, lon: coords.longitude });
      setUseNearby(true);
    } catch (error) {
      setLocationError(error instanceof Error ? error.message : "位置情報取得に失敗しました");
    }
  }

  function handleClearLocation() {
    setUserLocation(null);
    setUseNearby(false);
    setLocationError(null);
  }

  const hasActiveFilters = keyword || area !== "すべて" || activeTags.length > 0;

  function shuffleArray<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  let displayStores = showFavoritesOnly ? stores.filter(s => favorites.includes(s.id)) : stores;
  if (useNearby && userLocation) {
    displayStores = displayStores
      .map(store => ({
        store,
        distance: store.latitude && store.longitude
          ? calculateDistance(userLocation.lat, userLocation.lon, store.latitude, store.longitude)
          : Infinity
      }))
      .sort((a, b) => a.distance - b.distance)
      .map(({ store }) => store);
  } else if (!hasActiveFilters && !showFavoritesOnly) {
    displayStores = shuffleArray(displayStores);
  }
  const visibleCount = showFavoritesOnly
    ? favorites.filter(id => stores.some(s => s.id === id)).length
    : total;
  const isInitialLoading = loading && stores.length === 0;

  return (
    <div>
      {/* 検索を常に上部に固定 — スクロールしても消えない compact search bar */}
      <div className="sticky top-0 z-40 -mx-4 border-b border-line bg-paper/95 px-4 pb-3 pt-4 backdrop-blur-md sm:mx-0 sm:rounded-b-xl sm:border sm:border-t-0 sm:px-5">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <svg
              viewBox="0 0 24 24"
              className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="7" />
              <path strokeLinecap="round" d="m20 20-3.2-3.2" />
            </svg>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="お店の名前やメニューで探す"
              aria-label="お店の名前やメニューで探す"
              className="w-full rounded-lg border border-line bg-surface py-2.5 pl-10 pr-4 text-base text-ink placeholder:text-graphite/60 focus:border-ink focus:outline-none focus:ring-2 focus:ring-rust/25"
              style={{ WebkitAppearance: "none", appearance: "none" }}
            />
          </div>
          <button
            onClick={() => setShowFilter((v) => !v)}
            aria-expanded={showFilter}
            aria-label={showFilter ? "詳細フィルターを閉じる" : "詳細フィルターを開く"}
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border transition-colors ${
              showFilter || hasActiveFilters
                ? "border-ink bg-ink text-paper"
                : "border-line bg-surface text-ink hover:border-ink/40"
            }`}
            title="絞り込み"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
              <path strokeLinecap="round" d="M4 6h16M8 12h8M11 18h2" />
            </svg>
          </button>
        </div>

        {/* カテゴリタブ（隠れ家・古民家・新規開店など）横スクロール */}
        {discoveryTags.length > 0 && (
          <div className="no-scrollbar mt-3 flex gap-4 overflow-x-auto">
            {discoveryTags.map((tag) => {
              const active = activeTags.includes(tag);
              return (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  aria-pressed={active}
                  className={`shrink-0 whitespace-nowrap border-b-2 pb-2 pt-1 text-sm font-medium tracking-wide transition-colors ${
                    active
                      ? "border-rust text-ink"
                      : "border-transparent text-graphite hover:text-ink"
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 詳細フィルターパネル（折りたたみ） */}
      {showFilter && (
        <div className="-mx-4 mb-8 border-b border-line bg-surface px-4 py-5 sm:mx-0 sm:mt-4 sm:rounded-xl sm:border sm:px-6">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-graphite">エリア</p>
            <select
              value={area}
              onChange={(e) => setArea(e.target.value)}
              className="w-full rounded-lg border border-line bg-paper px-4 py-2.5 text-sm text-ink focus:border-ink focus:outline-none focus:ring-2 focus:ring-rust/25 sm:w-56"
            >
              {areas.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>

          {menus.length > 0 && (
            <div className="mt-5">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-graphite">タグで絞り込む</p>
              <div className="flex flex-wrap gap-2">
                {menus.slice(0, 12).map((tag) => {
                  const active = activeTags.includes(tag);
                  return (
                    <button
                      key={tag}
                      onClick={() => toggleTag(tag)}
                      aria-pressed={active}
                      className={`rounded-full border px-3 py-1.5 text-xs font-medium tracking-wide transition-colors ${
                        active
                          ? "border-ink bg-ink text-paper"
                          : "border-line bg-paper text-graphite hover:border-ink/40 hover:text-ink"
                      }`}
                    >
                      {tag}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <Link
            href="/nearby"
            className="mt-5 flex items-center justify-between gap-2 rounded-lg border border-line px-4 py-3 text-sm text-ink transition-colors hover:border-ink/40"
          >
            <span className="flex items-center gap-2">
              <svg viewBox="0 0 24 24" className="h-4 w-4 text-rust" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21s7-6.6 7-11.5a7 7 0 1 0-14 0C5 14.4 12 21 12 21Z" />
                <circle cx="12" cy="9.5" r="2.2" />
              </svg>
              現在地周辺を検索
            </span>
            <span className="text-graphite">→</span>
          </Link>

          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="mt-4 w-full rounded-lg border border-line bg-paper px-4 py-2.5 text-sm font-medium text-graphite transition-colors hover:border-ink/40 hover:text-ink"
            >
              検索条件をリセット
            </button>
          )}
        </div>
      )}

      <div className="mb-4 mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-graphite">
            {isInitialLoading
              ? "検索中…"
              : showFavoritesOnly
              ? `${visibleCount}件のお気に入り`
              : `${visibleCount}件のお店が見つかりました`}
          </p>
          {userLocation && (
            <p className="mt-0.5 text-xs font-medium text-rust">現在地周辺を表示中</p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {!userLocation ? (
            <button
              onClick={handleRequestLocation}
              className="rounded-lg border border-line bg-surface px-3 py-1.5 text-xs font-medium text-graphite transition-colors hover:border-ink/40 hover:text-ink"
            >
              近くのお店を表示
            </button>
          ) : (
            <button
              onClick={handleClearLocation}
              className="rounded-lg border border-rust bg-rust-tint px-3 py-1.5 text-xs font-medium text-rust-dark transition-colors hover:bg-rust-tint/70"
            >
              ✕ 現在地をクリア
            </button>
          )}
          {showFavoritesOnly && (
            <button
              onClick={() => setShowFavoritesOnly(false)}
              className="rounded-lg bg-ink px-3 py-2 text-xs font-medium text-paper transition-colors hover:bg-ink/85"
            >
              お気に入りのみ ✕
            </button>
          )}
        </div>
      </div>

      {locationError && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {locationError}
        </div>
      )}

      {isInitialLoading ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-line bg-surface px-6 py-16 text-center">
          <span className="h-2 w-2 animate-pulse rounded-full bg-rust" aria-hidden="true" />
          <p className="max-w-sm text-sm leading-relaxed text-graphite">
            <span className="font-semibold text-ink">豆知識　</span>
            {trivia}
          </p>
        </div>
      ) : visibleCount === 0 ? (
        <div className="rounded-xl border border-dashed border-line bg-surface py-16 text-center text-graphite">
          条件に合うお店が見つかりませんでした。キーワードや絞り込みを変えてみてください。
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 pb-16 sm:grid-cols-2 lg:grid-cols-3">
            {displayStores.map((store) => (
              <StoreCard
                key={store.id}
                store={store}
                keyword={keyword}
                area={area}
                activeTags={activeTags}
                distance={distanceMap[store.id]}
              />
            ))}
          </div>

          {hasMore && (
            <div className="pb-16 text-center">
              <button
                onClick={() => loadStores(stores.length)}
                disabled={loading}
                className="rounded-lg bg-rust px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-rust-dark disabled:opacity-50"
              >
                {loading ? "読み込み中…" : "もっと見る"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
