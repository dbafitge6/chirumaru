"use client";

import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import type { Store } from "@/lib/types";
import StoreCard from "./StoreCard";
import { getGeolocation, calculateDistance } from "@/lib/geolocation";

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
  const [showFilter, setShowFilter] = useState(true);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [menus, setMenus] = useState<string[]>([]);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [useNearby, setUseNearby] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
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
        console.log("Fetched tags:", data);
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

  return (
    <div>
      {/* Toggle button - ヘッダー下の右側 */}
      <button
        onClick={() => setShowFilter(!showFilter)}
        className="fixed right-4 top-20 z-[9999] flex h-10 w-10 items-center justify-center rounded-full bg-terracotta/70 text-white hover:bg-terracotta/90 transition-colors sm:block"
        title={showFilter ? "フィルターを隠す" : "フィルターを表示"}
      >
        {showFilter ? "✕" : "🔍"}
      </button>

      {showFilter && (
      <div className="sticky top-0 z-50 -mx-4 mb-8 border-b border-umber/10 bg-cream/90 px-4 py-4 backdrop-blur-md sm:mx-0 sm:rounded-3xl sm:border sm:px-6 sm:shadow-sm">
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

        <div className="mt-3 grid grid-cols-2 gap-2">
          {menus.slice(0, 10).map((tag) => {
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

        <div className="mt-4 rounded-lg border border-terracotta/20 bg-terracotta/5 p-4">
          <Link
            href="/nearby"
            className="flex items-center justify-between gap-2 font-medium text-terracotta hover:text-clay transition-colors"
          >
            <span>📍 現在地周辺を検索</span>
            <span>→</span>
          </Link>
          <p className="mt-1 text-xs text-umber/60">
            あなたの周辺のカフェ・パン屋を見つけよう
          </p>
        </div>

        {(keyword || area !== "すべて" || activeTags.length > 0) && (
          <button
            onClick={clearAllFilters}
            className="mt-3 w-full rounded-full border border-umber/15 bg-white px-4 py-2 text-sm font-medium text-umber hover:bg-umber/5 transition-colors"
          >
            ✕ 検索条件をリセット
          </button>
        )}
      </div>
      )}

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-umber/60">
            {showFavoritesOnly ? `${favorites.filter(id => stores.some(s => s.id === id)).length}件のお気に入り` : `${total}件のお店が見つかりました`}
          </p>
          {userLocation && (
            <p className="text-xs text-terracotta">📍 現在地周辺を表示中</p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {!userLocation ? (
            <button
              onClick={handleRequestLocation}
              className="rounded-full border border-umber/15 bg-white px-3 py-1.5 text-xs font-medium text-umber/70 hover:border-terracotta/50 transition-colors"
            >
              📍 近くのお店を表示
            </button>
          ) : (
            <button
              onClick={handleClearLocation}
              className="rounded-full border border-terracotta bg-terracotta/10 px-3 py-1.5 text-xs font-medium text-terracotta hover:bg-terracotta/20 transition-colors"
            >
              ✕ 現在地をクリア
            </button>
          )}
          {showFavoritesOnly && (
            <button
              onClick={() => setShowFavoritesOnly(false)}
              className="rounded-full bg-terracotta px-3 py-1.5 text-xs font-medium text-white hover:bg-clay transition-colors"
            >
              ❤️ お気に入りのみ ✕
            </button>
          )}
        </div>
      </div>

      {locationError && (
        <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {locationError}
        </div>
      )}

      {(showFavoritesOnly ? favorites.filter(id => stores.some(s => s.id === id)).length === 0 : total === 0) ? (
        <div className="rounded-3xl border border-dashed border-umber/20 bg-white/50 py-16 text-center text-umber/50">
          条件に合うお店が見つかりませんでした。キーワードや絞り込みを変えてみてください。
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-5 pb-16 sm:grid-cols-2 lg:grid-cols-3">
            {(() => {
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
              }
              return displayStores.map((store) => (
                <StoreCard
                  key={store.id}
                  store={store}
                  keyword={keyword}
                  area={area}
                  activeTags={activeTags}
                  distance={distanceMap[store.id]}
                />
              ));
            })()}
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
