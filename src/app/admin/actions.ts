"use server";

import { revalidatePath } from "next/cache";
import { addStorePhoto } from "@/lib/airtable";

export async function approvePhoto(storeId: string, photoUrl: string) {
  await addStorePhoto(storeId, photoUrl);
  revalidatePath("/admin");
  revalidatePath("/");
  revalidatePath(`/store/${storeId}`);
}
