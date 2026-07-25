"use client";

import { useMemo, useState, useTransition } from "react";
import type { PhotoSubmission } from "@/lib/sheet";
import type { StoreOption } from "@/lib/airtable";
import { approvePhoto } from "@/app/admin/actions";

function guessStoreId(storeName: string, stores: StoreOption[]): string {
  const name = storeName.trim();
  if (!name) return "";
  const exact = stores.find((s) => s.name === name);
  if (exact) return exact.id;
  const partial = stores.find(
    (s) => s.name.includes(name) || name.includes(s.name)
  );
  return partial?.id ?? "";
}

function PhotoRow({
  photoUrl,
  submissionStoreName,
  stores,
}: {
  photoUrl: string;
  submissionStoreName: string;
  stores: StoreOption[];
}) {
  const [selectedId, setSelectedId] = useState(() =>
    guessStoreId(submissionStoreName, stores)
  );
  const [isPending, startTransition] = useTransition();
  const [done, setDone] = useState(false);

  const alreadyAdded = useMemo(
    () => stores.some((s) => s.photoUrls.includes(photoUrl)),
    [stores, photoUrl]
  );

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-umber/10 bg-white/70 p-3">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={photoUrl}
        alt=""
        className="h-20 w-20 shrink-0 rounded-lg object-cover"
      />
      <select
        value={selectedId}
        onChange={(e) => setSelectedId(e.target.value)}
        disabled={done || isPending}
        className="min-w-0 flex-1 rounded-full border border-umber/15 bg-white px-3 py-1.5 text-sm text-umber disabled:opacity-50"
      >
        <option value="">店舗を選択…</option>
        {stores.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
            {s.area ? `（${s.area}）` : ""}
          </option>
        ))}
      </select>
      <button
        disabled={!selectedId || done || isPending || alreadyAdded}
        onClick={() => {
          if (!selectedId) return;
          startTransition(async () => {
            await approvePhoto(selectedId, photoUrl);
            setDone(true);
          });
        }}
        className="shrink-0 rounded-full bg-terracotta px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-clay disabled:cursor-not-allowed disabled:bg-umber/20 disabled:text-umber/50"
      >
        {alreadyAdded || done ? "✓ 使用中" : isPending ? "処理中…" : "使う"}
      </button>
    </div>
  );
}

export default function AdminBrowser({
  submissions,
  stores,
}: {
  submissions: PhotoSubmission[];
  stores: StoreOption[];
}) {
  if (submissions.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-umber/20 bg-white/50 p-8 text-center text-sm text-umber/50">
        まだ写真の投稿がありません。
      </p>
    );
  }

  return (
    <div className="space-y-5">
      {[...submissions].reverse().map((sub) => (
        <div
          key={sub.rowIndex}
          className="rounded-3xl border border-umber/10 bg-cream/60 p-4"
        >
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2 text-sm">
            <div>
              <span className="font-display font-bold text-umber">
                {sub.storeName || "（店舗名未入力）"}
              </span>
              <span className="ml-2 text-umber/50">
                投稿者: {sub.submitterName || "匿名"}
              </span>
            </div>
            <span className="text-xs text-umber/40">{sub.timestamp}</span>
          </div>
          {sub.comment && (
            <p className="mb-3 text-sm text-umber/70">{sub.comment}</p>
          )}
          {sub.photoUrls.length === 0 ? (
            <p className="text-sm text-umber/40">写真なし</p>
          ) : (
            <div className="space-y-2">
              {sub.photoUrls.map((url) => (
                <PhotoRow
                  key={url}
                  photoUrl={url}
                  submissionStoreName={sub.storeName}
                  stores={stores}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
