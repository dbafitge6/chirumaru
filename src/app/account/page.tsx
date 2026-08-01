'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Store } from '@/lib/types';
import StoreCard from '@/components/StoreCard';
import SiteHeader from '@/components/SiteHeader';
import SiteFooter from '@/components/SiteFooter';

export default function AccountPage() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [favoriteStores, setFavoriteStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = JSON.parse(localStorage.getItem('favorites') || '[]');
    setFavorites(saved);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const loadFavorites = async () => {
      try {
        const allStores: Store[] = [];
        let offset = 0;
        let hasMore = true;

        while (hasMore) {
          const res = await fetch(`/api/stores?offset=${offset}`);
          const data = await res.json();
          allStores.push(...(data.items || []));
          hasMore = data.hasMore || false;
          offset += (data.items?.length || 0);
        }

        const favorited = allStores.filter((store) => favorites.includes(store.id));
        setFavoriteStores(favorited);
      } catch (error) {
        console.error('Failed to load favorite stores:', error);
      } finally {
        setLoading(false);
      }
    };

    loadFavorites();
  }, [favorites, mounted]);

  if (!mounted) return null;

  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <div className="mb-8">
            <h1 className="font-display text-3xl font-black text-umber sm:text-4xl">
              アカウント
            </h1>
            <p className="mt-2 text-umber/60">
              お気に入りとアカウント情報を管理
            </p>
          </div>

          {/* Favorites Section */}
          <div className="rounded-3xl border border-umber/10 bg-white/60 p-6 sm:p-8">
            <div className="mb-6 flex items-center gap-3">
              <span className="text-2xl">❤️</span>
              <h2 className="font-display text-2xl font-bold text-umber">
                お気に入り ({favorites.length})
              </h2>
            </div>

            {loading ? (
              <p className="text-center text-umber/60">読み込み中...</p>
            ) : favorites.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-umber/20 bg-white/50 py-12 text-center">
                <p className="text-umber/50">
                  まだお気に入りがありません
                </p>
                <Link
                  href="/"
                  className="mt-4 inline-block rounded-full bg-terracotta px-6 py-2.5 text-sm font-medium text-white hover:bg-clay transition-colors"
                >
                  カフェを探す
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {favoriteStores.map((store) => (
                  <StoreCard
                    key={store.id}
                    store={store}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
