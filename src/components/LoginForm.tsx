'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const DEFAULT_USERS = {
  'test@example.com': 'password123',
  'demo@chirumaru.jp': 'demo123456',
  'user@chirumaru.jp': 'user123',
};

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [testUsers, setTestUsers] = useState<Record<string, string>>(DEFAULT_USERS);
  const router = useRouter();

  useEffect(() => {
    const saved = localStorage.getItem('mockUsers');
    if (saved) {
      setTestUsers(JSON.parse(saved));
    } else {
      setTestUsers(DEFAULT_USERS);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // モック認証（Airtable API が使用可能になるまでの暫定実装）
      if (!email || !password) {
        setError('メールアドレスとパスワードを入力してください');
        setLoading(false);
        return;
      }

      if (isSignUp) {
        // アカウント作成：新規メールなら成功
        if (testUsers[email]) {
          setError('このメールアドレスは既に登録されています');
          setLoading(false);
          return;
        }
        // テストユーザーに追加
        const updated = { ...testUsers, [email]: password };
        setTestUsers(updated);
        localStorage.setItem('mockUsers', JSON.stringify(updated));
        localStorage.setItem('userId', `user_${Date.now()}`);
        localStorage.setItem('userEmail', email);
        router.push('/');
      } else {
        // ログイン：テストユーザーをチェック
        if (testUsers[email] === password) {
          localStorage.setItem('userId', `user_${email.split('@')[0]}`);
          localStorage.setItem('userEmail', email);
          router.push('/');
        } else {
          setError('メールアドレスまたはパスワードが間違っています');
        }
      }
    } catch (err) {
      setError('Something went wrong');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">
        {isSignUp ? 'アカウント作成' : 'ログイン'}
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            メールアドレス
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta"
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            パスワード
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-terracotta text-white py-2 rounded-lg font-medium hover:bg-clay disabled:opacity-50"
        >
          {loading ? '処理中...' : isSignUp ? '作成' : 'ログイン'}
        </button>
      </form>

      <div className="mt-4 text-center">
        <button
          onClick={() => setIsSignUp(!isSignUp)}
          className="text-sm text-terracotta hover:underline"
        >
          {isSignUp
            ? 'ログインはこちら'
            : 'アカウント作成はこちら'}
        </button>
      </div>
    </div>
  );
}
