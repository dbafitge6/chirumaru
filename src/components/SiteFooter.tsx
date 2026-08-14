import Link from 'next/link';

export default function SiteFooter() {
  return (
    <footer className="border-t border-umber/10 bg-cream mt-auto">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-sm text-umber/60">
            © 2024 ちるまる
          </p>
          <nav className="flex gap-6 text-sm">
            <Link
              href="/articles"
              className="text-umber/60 hover:text-umber transition-colors"
            >
              読みもの
            </Link>
            <a
              href="https://instagram.com"
              className="text-umber/60 hover:text-umber transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Instagram
            </a>
          </nav>
        </div>
      </div>
    </footer>
  );
}
