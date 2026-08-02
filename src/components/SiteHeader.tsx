'use client';

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

export default function SiteHeader() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/auth/callback`;
    const scope = 'openid profile email';
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=${scope}`;
    window.location.href = authUrl;
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem('authToken');
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
          {isLoggedIn ? (
            <>
              <button
                onClick={handleLogout}
                className="px-3 py-2 text-sm font-medium text-umber hover:text-clay transition-colors"
              >
                ログアウト
              </button>
              <Link
                href="/account"
                className="flex h-10 w-10 items-center justify-center rounded-full hover:bg-terracotta/10 transition-colors"
                title="アカウント"
              >
                👤
              </Link>
            </>
          ) : (
            <>
              <button
                onClick={handleLogin}
                className="px-3 py-2 text-sm font-medium text-umber hover:text-clay transition-colors"
              >
                ログイン
              </button>
              <Link
                href="/account"
                className="flex h-10 w-10 items-center justify-center rounded-full hover:bg-terracotta/10 transition-colors"
                title="アカウント"
              >
                👤
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
