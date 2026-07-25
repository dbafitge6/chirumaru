import { getPhotoSubmissions } from "@/lib/sheet";
import { getStoreOptions } from "@/lib/airtable";
import AdminBrowser from "@/components/AdminBrowser";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  let submissions: Awaited<ReturnType<typeof getPhotoSubmissions>> = [];
  let stores: Awaited<ReturnType<typeof getStoreOptions>> = [];
  let loadError: string | null = null;

  try {
    [submissions, stores] = await Promise.all([
      getPhotoSubmissions(),
      getStoreOptions(),
    ]);
  } catch (e) {
    loadError = e instanceof Error ? e.message : "不明なエラーが発生しました";
  }

  return (
    <main className="min-h-screen bg-cream px-4 py-8 text-umber sm:px-6">
      <div className="mx-auto max-w-2xl">
        <h1 className="font-display text-2xl font-bold text-clay">
          写真管理
        </h1>
        <p className="mt-1 text-sm text-umber/60">
          投稿された写真を店舗に割り当てて公開します。
        </p>

        <div className="mt-6">
          {loadError ? (
            <div className="rounded-2xl border border-dashed border-clay/30 bg-white/60 p-6 text-sm text-clay">
              データを読み込めませんでした。
              <br />
              <span className="text-umber/50">({loadError})</span>
            </div>
          ) : (
            <AdminBrowser submissions={submissions} stores={stores} />
          )}
        </div>
      </div>
    </main>
  );
}
