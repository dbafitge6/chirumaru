'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import SiteHeader from '@/components/SiteHeader';
import SiteFooter from '@/components/SiteFooter';

export default function PasswordResetPage() {
  const [step, setStep] = useState<'email' | 'reset'>('email');
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // メールアドレスがテストユーザーに存在するか確認
      const mockUsers = JSON.parse(localStorage.getItem('mockUsers') || '{}');
      if (!mockUsers[email]) {
        setError('このメールアドレスは登録されていません');
        setLoading(false);
        return;
      }

      // リセットコード生成して保存
      const resetCode = Math.random().toString(36).substring(2, 10).toUpperCase();
      localStorage.setItem(`resetCode_${email}`, resetCode);
      localStorage.setItem(`resetCodeTime_${email}`, Date.now().toString());

      setStep('reset');
    } catch (err) {
      setError('エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!newPassword || !confirmPassword) {
      setError('パスワードを入力してください');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('パスワードが一致しません');
      return;
    }

    if (newPassword.length < 6) {
      setError('パスワードは6文字以上である必要があります');
      return;
    }

    try {
      setLoading(true);

      // リセットコード確認（実装簡略版）
      const resetCode = localStorage.getItem(`resetCode_${email}`);
      if (!resetCode) {
        setError('リセットコードが見つかりません。もう一度お試しください');
        return;
      }

      // パスワード更新
      const mockUsers = JSON.parse(localStorage.getItem('mockUsers') || '{}');
      mockUsers[email] = newPassword;
      localStorage.setItem('mockUsers', JSON.stringify(mockUsers));

      // リセットコード削除
      localStorage.removeItem(`resetCode_${email}`);
      localStorage.removeItem(`resetCodeTime_${email}`);

      router.push('/login?resetSuccess=true');
    } catch (err) {
      setError('パスワード更新に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <SiteHeader />
      <main className="flex-1">
        <section className="mx-auto max-w-md px-4 py-12 sm:px-6">
          <div className="rounded-3xl border border-umber/10 bg-white/60 p-8">
            <h1 className="font-display text-2xl font-bold text-umber mb-6">
              パスワードリセット
            </h1>

            {error && (
              <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
                {error}
              </div>
            )}

            {step === 'email' ? (
              <form onSubmit={handleEmailSubmit}>
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">
                    メールアドレス
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full rounded-full border border-umber/15 bg-white px-4 py-2.5 text-umber focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/30"
                    placeholder="example@chirumaru.jp"
                  />
                  <p className="mt-2 text-xs text-umber/60">
                    登録済みのメールアドレスを入力してください
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-terracotta text-white py-2.5 rounded-full font-medium hover:bg-clay disabled:opacity-50 transition-colors"
                >
                  {loading ? '処理中...' : 'リセットコードを送信'}
                </button>
              </form>
            ) : (
              <form onSubmit={handlePasswordReset}>
                <div className="mb-4 p-3 bg-terracotta/10 rounded text-sm text-terracotta">
                  ✓ メールアドレスが確認されました
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">
                    新しいパスワード
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    className="w-full rounded-full border border-umber/15 bg-white px-4 py-2.5 text-umber focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/30"
                    placeholder="新しいパスワード"
                  />
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">
                    パスワード確認
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full rounded-full border border-umber/15 bg-white px-4 py-2.5 text-umber focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/30"
                    placeholder="パスワード確認"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-terracotta text-white py-2.5 rounded-full font-medium hover:bg-clay disabled:opacity-50 transition-colors"
                >
                  {loading ? '処理中...' : 'パスワードをリセット'}
                </button>
              </form>
            )}

            <div className="mt-6 text-center">
              <Link
                href="/login"
                className="text-sm text-terracotta hover:underline"
              >
                ログインに戻る
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
