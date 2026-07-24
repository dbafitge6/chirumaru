import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="border-b border-umber/10 bg-cream/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-terracotta font-display text-lg font-bold text-white">
            ち
          </span>
          <span className="font-display text-xl font-bold text-clay">
            ちるまる
          </span>
        </Link>
        <span className="hidden text-sm text-umber/50 sm:block">
          新潟のカフェ・パン屋・スイーツ探し
        </span>
      </div>
    </header>
  );
}
