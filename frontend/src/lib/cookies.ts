import { cookies } from "next/headers";

// Forwards the browser's cookies (namely access_token) to the backend for
// server-to-server calls - the backend never sees the browser directly.
export async function getCookieHeader(): Promise<string> {
  return (await cookies()).toString();
}
