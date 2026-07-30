'use client';

import { GoogleOAuthProvider } from '@react-oauth/google';
import LoginForm from '@/components/LoginForm';

export default function LoginPage() {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <main className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <LoginForm />
        </div>
      </main>
    </GoogleOAuthProvider>
  );
}
