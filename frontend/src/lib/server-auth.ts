import "server-only";
import { NextRequest, NextResponse } from "next/server";

export type User = { id: number; nome: string; email: string; perfil: number };
type Tokens = { access: string; refresh: string };
const base = () => `${process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000"}/api/v1`;
const secure = () => process.env.AUTH_COOKIE_SECURE === "true" || (process.env.AUTH_COOKIE_SECURE !== "false" && process.env.NODE_ENV === "production");
const options = { httpOnly: true, sameSite: "lax" as const, path: "/" };

export function sameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  try {
    const url = new URL(origin);
    return (url.protocol === "http:" || url.protocol === "https:") && url.host === request.headers.get("host");
  } catch { return false; }
}
export function setTokens(response: NextResponse, tokens: Tokens) {
  response.cookies.set("bf_access", tokens.access, { ...options, secure: secure(), maxAge: 15 * 60 });
  response.cookies.set("bf_refresh", tokens.refresh, { ...options, secure: secure(), maxAge: 7 * 24 * 60 * 60 });
}
export function clearTokens(response: NextResponse) {
  for (const name of ["bf_access", "bf_refresh"]) response.cookies.set(name, "", { ...options, secure: secure(), maxAge: 0 });
}
export async function backend(path: string, init: RequestInit = {}) {
  return fetch(`${base()}${path}`, { ...init, cache: "no-store", signal: AbortSignal.timeout(10000), headers: { "Content-Type": "application/json", ...init.headers } });
}

// A rotação deve ser compartilhada por solicitações simultâneas do mesmo processo.
const refreshing = new Map<string, Promise<{ status: number; tokens?: Tokens }>>();
export async function refreshOnce(refresh: string) {
  const existing = refreshing.get(refresh);
  if (existing) return existing;
  const promise = (async () => {
    const result = await backend("/auth/refresh", { method: "POST", body: JSON.stringify({ refresh }) });
    if (!result.ok) return { status: result.status };
    const tokens = await result.json() as Tokens;
    return { status: result.status, tokens };
  })();
  refreshing.set(refresh, promise);
  try { return await promise; } finally { refreshing.delete(refresh); }
}
export async function identity(access: string) {
  const response = await backend("/me", { headers: { Authorization: `Bearer ${access}` } });
  return { response, user: response.ok ? await response.json() as User : null };
}
