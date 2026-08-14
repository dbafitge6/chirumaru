'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import type { Store } from '@/lib/types';
import { getGeolocation, calculateDistance } from '@/lib/geolocation';
import StoreCard from '@/components/StoreCard';
import SiteHeader from '@/components/SiteHeader';

export default function NearbyPage() {
  const router = useRouter();
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [maxDistance, setMaxDistance] = useState(5); // km

  // ページ初期化時に sessionStorage から状態を復元
  useEffect(() => {
    const savedLocation = sessionStorage.getItem('nearbySearchLocation');
    if (savedLocation) {
      try {
        const location = JSON.parse(savedLocation);
        setUserLocation(location);
      } catch (e) {
        console.error('Failed to restore location:', e);
      }
    }
  }, []);

  // 位置情報が変わったら sessionStorage に保存
  useEffect(() => {
    if (userLocation) {
      sessionStorage.setItem('nearbySearchLocation', JSON.stringify(userLocation));
    }
  }, [userLocation]);

  // 位置情報を取得
  const handleRequestLocation = async () => {
    setLocationError(null);
    setLoading(true);
    try {
      const coords = await getGeolocation();
      setUserLocation({ lat: coords.latitude, lon: coords.longitude });
    } catch (error) {
      setLocationError(error instanceof Error ? error.message : '位置情報取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // ユーザー現在地に基づいてお店を読み込む
  useEffect(() => {
    if (!userLocation) return;

    const loadNearbyStores = async () => {
      setLoading(true);
      try {
        // ページネーション対応ですべての店舗を取得
        const allStores = [];
        let offset = 0;

        while (true) {
          const res = await fetch(`/api/stores?offset=${offset}`);
          const data = await res.json();
          const items = data.items || [];

          if (items.length === 0) break;

          allStores.push(...items);
          offset += items.length;
        }

        // 距離を計算してソート
        const withDistance = allStores
          .map((store: Store) => ({
            store,
            distance: store.latitude && store.longitude
              ? calculateDistance(userLocation.lat, userLocation.lon, store.latitude, store.longitude)
              : Infinity
          }))
          .filter(({ distance }: { distance: number }) => distance <= maxDistance)
          .sort((a: { distance: number }, b: { distance: number }) => a.distance - b.distance);

        setStores(withDistance.map(({ store }: { store: Store }) => store));
      } catch (error) {
        console.error('Failed to load nearby stores:', error);
        setLocationError('お店の読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };

    loadNearbyStores();
  }, [userLocation, maxDistance]);

  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <div className="mb-8">
            <h1 className="font-display text-3xl font-black text-umber sm:text-4xl">
              現在地から探す
            </h1>
            <p className="mt-2 text-umber/60">
              あなたの周辺のカフェ・パン屋・スイーツ店を見つけよう
            </p>
          </div>

          {!userLocation ? (
            <div className="rounded-3xl border border-umber/10 bg-white/60 p-8 text-center">
              <p className="mb-4 text-umber/70">位置情報を許可して、周辺のお店を検索します</p>
              <button
                onClick={handleRequestLocation}
                disabled={loading}
                className="rounded-full bg-terracotta px-8 py-3 text-white hover:bg-clay disabled:opacity-50 transition-colors"
              >
                {loading ? '取得中...' : '📍 位置情報を許可する'}
              </button>
            </div>
          ) : (
            <>
              <div className="mb-6 flex items-center justify-between rounded-2xl border border-terracotta/20 bg-terracotta/5 p-4">
                <div className="text-sm text-umber">
                  <p className="font-medium">📍 現在地が取得されました</p>
                  <p className="text-xs text-umber/60">
                    {stores.length} 件のお店が見つかりました（{maxDistance}km 圏内）
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={maxDistance}
                    onChange={(e) => setMaxDistance(Number(e.target.value))}
                    className="rounded-full border border-umber/15 bg-white px-3 py-2 text-sm text-umber focus:border-terracotta focus:outline-none"
                  >
                    <option value={5}>5 km</option>
                    <option value={10}>10 km</option>
                    <option value={20}>20 km</option>
                    <option value={30}>30 km</option>
                    <option value={50}>50 km</option>
                  </select>
                  <button
                    onClick={() => setUserLocation(null)}
                    className="rounded-full border border-terracotta bg-terracotta/10 px-4 py-2 text-xs font-medium text-terracotta hover:bg-terracotta/20"
                  >
                    クリア
                  </button>
                </div>
              </div>

              {locationError && (
                <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700">
                  {locationError}
                </div>
              )}

              {loading ? (
                <div className="py-16 text-center text-umber/60">
                  読み込み中...
                </div>
              ) : stores.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-umber/20 bg-white/50 py-16 text-center text-umber/50">
                  {maxDistance}km 圏内にお店が見つかりませんでした。
                  <br />
                  検索範囲を広げてみてください。
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-5 pb-16 sm:grid-cols-2 lg:grid-cols-3">
                  {stores.map((store) => {
                    const distance = store.latitude && store.longitude
                      ? calculateDistance(userLocation.lat, userLocation.lon, store.latitude, store.longitude)
                      : undefined;
                    return (
                      <StoreCard key={store.id} store={store} distance={distance} />
                    );
                  })}
                </div>
              )}
            </>
          )}

          <div className="mt-12 rounded-2xl border border-umber/10 bg-white/60 p-6">
            <button
              onClick={() => router.back()}
              className="w-full text-center text-sm text-umber/70 hover:text-terracotta transition-colors"
            >
              <span className="font-medium text-terracotta hover:underline">← 戻る</span>
            </button>
          </div>
        </section>
      </main>
    </>
  );
}
