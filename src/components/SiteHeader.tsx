'use client';

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function SiteHeader() {
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const id = localStorage.getItem('userId');
    const email = localStorage.getItem('userEmail');
    setUserId(id);
    setUserEmail(email);
  }, []);

  if (!mounted) return null;

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    setUserId(null);
    setUserEmail(null);
  };

  return (
    <header className="border-b border-umber/10 bg-cream/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/icon-original.png"
            alt="ちるまる"
            width={36}
            height={36}
            unoptimized
            priority
            className="h-9 w-9 rounded-full object-cover"
          />
          <span className="font-display text-xl font-bold text-clay">
            ちるまる
          </span>
        </Link>
        <span className="hidden text-sm text-umber/50 sm:block">
          新潟のカフェ・パン屋・スイーツ探し
        </span>

        <div className="flex items-center gap-3">
          {userId ? (
            <>
              <span className="text-sm text-umber">{userEmail}</span>
              <button
                onClick={handleLogout}
                className="rounded-lg bg-clay/10 px-3 py-2 text-sm font-medium text-clay hover:bg-clay/20"
              >
                ログアウト
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="rounded-lg bg-terracotta px-4 py-2 text-sm font-medium text-white hover:bg-clay"
            >
              ログイン
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
