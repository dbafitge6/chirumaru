import Link from "next/link";
import Script from "next/script";

export default function SiteFooter() {
  return (
    <>
      <footer className="mt-16 border-t border-umber/10 bg-blush/40 py-8">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col items-center justify-center gap-4 text-xs text-umber/50 sm:gap-6">
            <div className="flex gap-6">
              <Link href="/privacy" className="hover:text-umber/70 transition-colors">
                プライバシーポリシー
              </Link>
              <Link href="/company-info" className="hover:text-umber/70 transition-colors">
                運営者情報
              </Link>
            </div>
            <p>© {new Date().getFullYear()} ちるまる — 新潟のお店探し</p>
          </div>
        </div>
      </footer>
      <Script
        async
        src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9251250149426348"
        crossOrigin="anonymous"
      />
    </>
  );
}
