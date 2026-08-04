import type { Store } from "./types";

const BASE_ID = process.env.AIRTABLE_BASE_ID ?? "appyyoKM7RprQRht8";
const TABLE_ID = process.env.AIRTABLE_TABLE_ID ?? "tblcOdcqCxzb7kX0e";
const API_KEY = process.env.AIRTABLE_API_KEY;

type AirtableRecord = {
  id: string;
  createdTime: string;
  fields: Record<string, string>;
};

type AirtableListResponse = {
  records: AirtableRecord[];
  offset?: string;
};

function splitTags(raw: string | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(/[\/,、]/)
    .map((t) => t.trim())
    .filter(Boolean);
}

function splitPhotoUrls(raw: string | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(/[\n,]/)
    .map((u) => u.trim())
    .map((u) => {
      if (u.includes('drive.google.com/open?id=')) {
        const id = u.match(/id=([^&]+)/)?.[1];
        return id ? `https://drive.google.com/uc?export=view&id=${id}` : u;
      }
      return u;
    })
    .filter(Boolean);
}

function toStore(record: AirtableRecord): Store {
  const f = record.fields;
  const photoUrls = splitPhotoUrls(f["Photos/Logo"]);
  return {
    id: record.id,
    name: f["Store Name"] ?? "",
    address: f["Address"] ?? "",
    phone: f["電話番号"] ?? "",
    hours: f["Business Hours"] ?? "",
    photoUrl: photoUrls[0] ?? "",
    photoUrls,
    tags: splitTags(f["Tags"]),
    area: f["Area"] ?? "",
    website: f["Website"] ?? "",
    mapUrl: f["Map Location"] ?? "",
    memo: f["一言メモ"] ?? "",
    menu: f["メニュー"] ?? "",
    updatedAt: f["情報更新日"] ?? "",
    latitude: f["Latitude"] ? parseFloat(f["Latitude"]) : undefined,
    longitude: f["Longitude"] ? parseFloat(f["Longitude"]) : undefined,
  };
}

/**
 * Fetches every store record from the Stores table, paginating through
 * Airtable's 100-record-per-page limit automatically.
 *
 * Requires AIRTABLE_API_KEY (a Personal Access Token with data.records:read
 * scope on this base) to be set as an environment variable. Never hard-code
 * the token here — set it in `.env.local` locally and in your hosting
 * provider's environment variable settings in production.
 */
export async function getAllStores(): Promise<Store[]> {
  if (!API_KEY) {
    throw new Error(
      "AIRTABLE_API_KEY is not set. Add it to .env.local (see .env.local.example)."
    );
  }

  const records: AirtableRecord[] = [];
  let offset: string | undefined;

  do {
    const url = new URL(`https://api.airtable.com/v0/${BASE_ID}/${TABLE_ID}`);
    url.searchParams.set("pageSize", "100");
    if (offset) url.searchParams.set("offset", offset);

    const res = await fetch(url.toString(), {
      headers: { Authorization: `Bearer ${API_KEY}` },
      // Revalidate the store list every 5 minutes so newly-added stores in
      // Airtable show up without needing a full redeploy.
      next: { revalidate: 300 },
    });

    if (!res.ok) {
      throw new Error(`Airtable API error: ${res.status} ${res.statusText}`);
    }

    const data: AirtableListResponse = await res.json();
    records.push(...data.records);
    offset = data.offset;
  } while (offset);

  // Sort by creation time (ascending) to match Airtable's display order
  records.sort((a, b) => new Date(a.createdTime).getTime() - new Date(b.createdTime).getTime());

  return records.map(toStore);
}

export async function getStoreById(id: string): Promise<Store | null> {
  const stores = await getAllStores();
  return stores.find((s) => s.id === id) ?? null;
}

/**
 * Appends a photo URL to a store's Photos/Logo field (newline-separated).
 * Requires a token with data.records:write scope — the admin page uses
 * ADMIN_AIRTABLE_API_KEY if set, falling back to AIRTABLE_API_KEY.
 */
export async function addStorePhoto(storeId: string, photoUrl: string): Promise<void> {
  const writeKey = process.env.ADMIN_AIRTABLE_API_KEY ?? API_KEY;
  if (!writeKey) {
    throw new Error("No Airtable API key configured for writes.");
  }

  // Fetch the current value first so we append rather than overwrite.
  const getRes = await fetch(
    `https://api.airtable.com/v0/${BASE_ID}/${TABLE_ID}/${storeId}`,
    { headers: { Authorization: `Bearer ${writeKey}` }, cache: "no-store" }
  );
  if (!getRes.ok) {
    throw new Error(`Failed to read store before update: ${getRes.status}`);
  }
  const current = await getRes.json();
  const existing: string = current.fields?.["Photos/Logo"] ?? "";
  const updated = existing ? `${existing}\n${photoUrl}` : photoUrl;

  const patchRes = await fetch(
    `https://api.airtable.com/v0/${BASE_ID}/${TABLE_ID}/${storeId}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${writeKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fields: { "Photos/Logo": updated } }),
    }
  );
  if (!patchRes.ok) {
    const body = await patchRes.text();
    throw new Error(`Failed to update store: ${patchRes.status} ${body}`);
  }
}

/**
 * Fetches a store along with the ids of its neighbors in the same order
 * stores appear on the homepage list, so the store detail page can offer
 * "previous" / "next" navigation.
 */
export async function getStoreWithNeighbors(
  id: string,
  filters?: { keyword?: string; area?: string; tags?: string[] }
): Promise<{ store: Store; prevId: string | null; nextId: string | null } | null> {
  const stores = await getAllStores();

  // Apply filters if provided (matching StoreBrowser logic)
  const filtered = filters ? stores.filter((s) => {
    if (filters.area && filters.area !== "すべて" && s.area !== filters.area) return false;
    if (filters.tags && filters.tags.length > 0 && !filters.tags.every((t) => s.tags.includes(t))) return false;
    if (filters.keyword) {
      const kw = filters.keyword.trim().toLowerCase();
      const haystack = `${s.name} ${s.memo} ${s.menu} ${s.tags.join(" ")}`.toLowerCase();
      if (!haystack.includes(kw)) return false;
    }
    return true;
  }) : stores;

  const index = filtered.findIndex((s) => s.id === id);
  if (index === -1) return null;

  return {
    store: filtered[index],
    prevId: index > 0 ? filtered[index - 1].id : null,
    nextId: index < filtered.length - 1 ? filtered[index + 1].id : null,
  };
}

export type StoreOption = { id: string; name: string; area: string; photoUrls: string[] };

/** Lightweight list of stores for the admin picker (id + name + area + existing photos). */
export async function getStoreOptions(): Promise<StoreOption[]> {
  const stores = await getAllStores();
  return stores
    .map((s) => ({ id: s.id, name: s.name, area: s.area, photoUrls: s.photoUrls }))
    .sort((a, b) => a.name.localeCompare(b.name, "ja"));
}
