import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-cream px-4 text-center">
      <div className="max-w-md">
        <h1 className="mb-4 text-6xl font-bold text-rust">404</h1>
        <h2 className="mb-2 text-2xl font-semibold text-umber">ページが見つかりません</h2>
        <p className="mb-8 text-umber/70">
          お探しのページは存在しないか、削除された可能性があります。
        </p>
        <Link
          href="/"
          className="inline-block rounded-lg bg-rust px-6 py-3 font-medium text-white transition-colors hover:bg-rust/90"
        >
          ホームに戻る
        </Link>
      </div>
    </div>
  );
}
