export default function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-umber/10 bg-blush/40 py-8">
      <div className="mx-auto max-w-6xl px-4 text-center text-xs text-umber/50 sm:px-6">
        © {new Date().getFullYear()} ちるまる — 新潟のお店探し
      </div>
    </footer>
  );
}
