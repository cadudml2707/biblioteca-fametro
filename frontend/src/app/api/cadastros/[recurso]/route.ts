import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

export async function POST(request: NextRequest, context: { params: Promise<{ recurso: string }> }) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  const { recurso } = await context.params;
  if (!["obras", "exemplares", "usuarios"].includes(recurso)) return NextResponse.json({ mensagem: "Não encontrado." }, { status: 404 });
  let entrada: { metodo?: string; id?: number; dados?: unknown; search?: string; page?: number };
  try { entrada = await request.json(); } catch { return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 }); }
  const { metodo, id, dados } = entrada;
  if (!["GET", "POST", "PATCH"].includes(metodo ?? "") || (id !== undefined && (!Number.isSafeInteger(id) || id <= 0)) || (metodo === "PATCH" && !id) || (metodo === "POST" && id)) {
    return NextResponse.json({ mensagem: "Operação inválida." }, { status: 400 });
  }
  const params = new URLSearchParams();
  if (recurso === "obras" && metodo === "GET" && !id) {
    if (entrada.search) params.set("search", entrada.search);
    if (entrada.page) params.set("page", String(entrada.page));
  }
  const path = `/${recurso}${id ? `/${id}` : ""}${params.size ? `?${params}` : ""}`;
  const refresh = request.cookies.get("bf_refresh")?.value;
  let access = request.cookies.get("bf_access")?.value;
  let tokens: { access: string; refresh: string } | undefined;
  try {
    const enviar = () => backend(path, {
      method: metodo,
      headers: { Authorization: `Bearer ${access}` },
      ...(metodo !== "GET" ? { body: JSON.stringify(dados) } : {}),
    });
    let result = access ? await enviar() : null;
    if ((!result || result.status === 401) && refresh) {
      const renewed = await refreshOnce(refresh);
      if (renewed.tokens) {
        tokens = renewed.tokens;
        access = tokens.access;
        result = await enviar();
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
    const response = NextResponse.json({ mensagem: "Não foi possível conectar ao servidor. Confira o estado antes de reenviar." }, { status: 503 });
    if (tokens) setTokens(response, tokens);
    return response;
  }
}
