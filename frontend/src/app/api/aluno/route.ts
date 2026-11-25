import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  let input: { action?: string; id?: number; search?: string; page?: number };
  try { input = await request.json(); } catch { return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 }); }
  const validId = Number.isSafeInteger(input.id) && (input.id ?? 0) > 0;
  let path: string;
  if (input.action === "catalogo") {
    const params = new URLSearchParams({ search: typeof input.search === "string" ? input.search : "", page: String(Number.isSafeInteger(input.page) && (input.page ?? 0) > 0 ? input.page : 1) });
    path = `/obras?${params}`;
  } else if (input.action === "detalhe" && validId) path = `/obras/${input.id}`;
  else if (input.action === "reservas" || (input.action === "reservar" && validId)) path = "/reservas";
  else return NextResponse.json({ mensagem: "Operação inválida." }, { status: 400 });
  let access = request.cookies.get("bf_access")?.value;
  const refresh = request.cookies.get("bf_refresh")?.value;
  let tokens: { access: string; refresh: string } | undefined;
  try {
    const send = () => backend(path, { method: input.action === "reservar" ? "POST" : "GET", headers: { Authorization: `Bearer ${access}` }, ...(input.action === "reservar" ? { body: JSON.stringify({ obra_id: input.id }) } : {}) });
    let result = access ? await send() : null;
    if ((!result || result.status === 401) && refresh) {
      const renewed = await refreshOnce(refresh);
      if (renewed.tokens) { tokens = renewed.tokens; access = tokens.access; result = await send(); }
      else if (renewed.status !== 401 && renewed.status !== 403) return NextResponse.json({ mensagem: "Não foi possível renovar a sessão." }, { status: 503 });
    }
    if (!result || result.status === 401) { const response = NextResponse.json({ mensagem: "Sessão encerrada." }, { status: 401 }); clearTokens(response); return response; }
    const response = NextResponse.json(await result.json(), { status: result.status });
    if (tokens) setTokens(response, tokens);
    return response;
  } catch {
    const response = NextResponse.json({ mensagem: "Não foi possível conectar. Consulte suas reservas antes de reenviar." }, { status: 503 });
    if (tokens) setTokens(response, tokens);
    return response;
  }
}
