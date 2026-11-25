import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  const search = request.nextUrl.searchParams.get("search") ?? "";
  const page = request.nextUrl.searchParams.get("page") ?? "1";
  const params = new URLSearchParams({ search, page });
  const access = request.cookies.get("bf_access")?.value;
  const refresh = request.cookies.get("bf_refresh")?.value;
  let tokens: { access: string; refresh: string } | undefined;
  try {
    let result = access ? await backend(`/obras?${params}`, { headers: { Authorization: `Bearer ${access}` } }) : null;
    if ((!result || result.status === 401) && refresh) {
      const renewed = await refreshOnce(refresh);
      if (renewed.tokens) {
        tokens = renewed.tokens;
        result = await backend(`/obras?${params}`, { headers: { Authorization: `Bearer ${tokens.access}` } });
      } else if (renewed.status !== 401 && renewed.status !== 403) {
        return NextResponse.json({ mensagem: "Não foi possível renovar a sessão." }, { status: 503 });
      }
    }
    if (!result || result.status === 401) {
      const response = NextResponse.json({ mensagem: "Sessão encerrada." }, { status: 401 });
      clearTokens(response);
      return response;
    }
    const response = NextResponse.json(await result.json(), { status: result.status });
    if (tokens) setTokens(response, tokens);
    return response;
  } catch {
    const response = NextResponse.json({ mensagem: "Não foi possível conectar ao servidor." }, { status: 503 });
    if (tokens) setTokens(response, tokens);
    return response;
  }
}
