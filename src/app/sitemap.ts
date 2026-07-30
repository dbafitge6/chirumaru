import type { MetadataRoute } from "next";
import { getAllStores } from "@/lib/airtable";

const BASE_URL = "https://www.chirumaru.jp";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      changeFrequency: "daily",
      priority: 1,
    },
  ];

  const stores = await getAllStores().catch(() => []);

  const storeRoutes: MetadataRoute.Sitemap = stores.map((store) => ({
    url: `${BASE_URL}/store/${store.id}`,
    changeFrequency: "weekly",
    priority: 0.7,
  }));

  return [...staticRoutes, ...storeRoutes];
}
