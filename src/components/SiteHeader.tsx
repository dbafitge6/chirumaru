'use client';

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";

export default function SiteHeader() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem('authToken');
    setIsLoggedIn(!!token);
  }, []);

  const handleLoginClick = () => {
    setShowLoginModal(true);
  };

  const handleGoogleLogin = () => {
    localStorage.setItem('authToken', 'logged-in-google-' + Date.now());
    setIsLoggedIn(true);
    setShowLoginModal(false);
  };

  const handleEmailLogin = () => {
    localStorage.setItem('authToken', 'logged-in-email-' + Date.now());
    setIsLoggedIn(true);
    setShowLoginModal(false);
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
                onClick={handleLoginClick}
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

      {showLoginModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-lg">
            <h2 className="text-xl font-bold text-umber mb-6">ログイン方法を選択</h2>

            <div className="space-y-3">
              <button
                onClick={handleGoogleLogin}
                className="w-full flex items-center justify-center gap-3 rounded-full border border-umber/15 bg-white px-4 py-3 font-medium text-umber hover:bg-umber/5 transition-colors"
              >
                <span>🔵</span>
                Googleでログイン
              </button>

              <button
                onClick={handleEmailLogin}
                className="w-full flex items-center justify-center gap-3 rounded-full bg-terracotta px-4 py-3 font-medium text-white hover:bg-clay transition-colors"
              >
                <span>✉️</span>
                メールアドレスでログイン
              </button>
            </div>

            <button
              onClick={() => setShowLoginModal(false)}
              className="mt-6 w-full rounded-full border border-umber/15 bg-white px-4 py-2 text-sm font-medium text-umber/60 hover:text-umber transition-colors"
            >
              キャンセル
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
