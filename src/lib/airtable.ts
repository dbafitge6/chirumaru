import type { Store } from "./types";

const BASE_ID = process.env.AIRTABLE_BASE_ID ?? "appyyoKM7RprQRht8";
const TABLE_ID = process.env.AIRTABLE_TABLE_ID ?? "tblcOdcqCxzb7kX0e";
const API_KEY = process.env.AIRTABLE_API_KEY;

type AirtableRecord = {
  id: string;
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

function toStore(record: AirtableRecord): Store {
  const f = record.fields;
  return {
    id: record.id,
    name: f["Store Name"] ?? "",
    address: f["Address"] ?? "",
    phone: f["電話番号"] ?? "",
    hours: f["Business Hours"] ?? "",
    photoUrl: f["Photos/Logo"] ?? "",
    tags: splitTags(f["Tags"]),
    area: f["Area"] ?? "",
    website: f["Website"] ?? "",
    mapUrl: f["Map Location"] ?? "",
    memo: f["一言メモ"] ?? "",
    menu: f["メニュー"] ?? "",
    updatedAt: f["情報更新日"] ?? "",
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

  return records.map(toStore);
}

export async function getStoreById(id: string): Promise<Store | null> {
  const stores = await getAllStores();
  return stores.find((s) => s.id === id) ?? null;
}
