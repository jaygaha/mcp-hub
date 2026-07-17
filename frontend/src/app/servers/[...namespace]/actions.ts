"use server";

import { revalidatePath } from "next/cache";

import { BACKEND_INTERNAL_URL } from "@/lib/config";
import { getCookieHeader } from "@/lib/cookies";
import type { ApiErrorBody } from "@/lib/types";

export type ActionResult = { ok: true } | { ok: false; error: string };

async function errorMessage(response: Response): Promise<string> {
  const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
  return body?.detail ?? "Something went wrong.";
}

export async function submitRating(namespace: string, score: number): Promise<ActionResult> {
  const response = await fetch(`${BACKEND_INTERNAL_URL}/api/v1/servers/${namespace}/ratings`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Cookie: await getCookieHeader() },
    body: JSON.stringify({ score }),
  });

  if (response.status === 401) {
    return { ok: false, error: "Log in with GitHub to rate this server." };
  }
  if (!response.ok) {
    return { ok: false, error: await errorMessage(response) };
  }

  revalidatePath(`/servers/${namespace}`);
  return { ok: true };
}

// Signature is (namespace, prevState, formData) specifically so
// submitReview.bind(null, namespace) produces the (prevState, formData)
// shape useActionState expects.
export async function submitReview(
  namespace: string,
  _prevState: ActionResult,
  formData: FormData,
): Promise<ActionResult> {
  const title = String(formData.get("title") ?? "").trim();
  const content = String(formData.get("content") ?? "").trim();
  if (!title || !content) {
    return { ok: false, error: "Title and review text are required." };
  }

  const response = await fetch(`${BACKEND_INTERNAL_URL}/api/v1/servers/${namespace}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Cookie: await getCookieHeader() },
    body: JSON.stringify({ title, content }),
  });

  if (response.status === 401) {
    return { ok: false, error: "Log in with GitHub to write a review." };
  }
  if (!response.ok) {
    return { ok: false, error: await errorMessage(response) };
  }

  revalidatePath(`/servers/${namespace}`);
  return { ok: true };
}
