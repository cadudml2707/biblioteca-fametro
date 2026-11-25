import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  let corpo: unknown;
  try { corpo = await request.json(); } catch { return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 }); }
  if (!corpo || typeof corpo !== "object" || Array.isArray(corpo)) return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 });
  const entrada = corpo as { recurso?: string; metodo?: string; id?: number; acao?: string; filtros?: Record<string, string>; dados?: unknown };
  const { recurso, metodo, id, acao, filtros, dados } = entrada;
  const valido = (metodo === "GET" && ["alunos", "reservas", "emprestimos", "exemplares", "obras"].includes(recurso ?? "") && !id && !acao)
    || (metodo === "POST" && recurso === "emprestimos" && !id && !acao)
    || (metodo === "POST" && recurso === "reservas" && Number.isSafeInteger(id) && (id ?? 0) > 0 && ["confirmar", "cancelar"].includes(acao ?? ""))
    || (metodo === "POST" && recurso === "emprestimos" && Number.isSafeInteger(id) && (id ?? 0) > 0 && acao === "devolver");
  if (!valido) return NextResponse.json({ mensagem: "Operação inválida." }, { status: 400 });
  const permitidos: Record<string, string[]> = { alunos: ["search", "page"], obras: ["search", "page"], reservas: ["usuario_id", "obra_id", "situacao"], emprestimos: ["usuario_id", "exemplar_id", "situacao"], exemplares: [] };
  const params = new URLSearchParams();
  if (metodo === "GET" && filtros && typeof filtros === "object") for (const [chave, valor] of Object.entries(filtros)) {
    if (permitidos[recurso!].includes(chave) && typeof valor === "string" && valor) params.set(chave, valor);
  }
  const path = `/${recurso}${id ? `/${id}` : ""}${acao ? `/${acao}` : ""}${params.size ? `?${params}` : ""}`;
  const refresh = request.cookies.get("bf_refresh")?.value;
  let access = request.cookies.get("bf_access")?.value;
  let tokens: { access: string; refresh: string } | undefined;
  try {
    const enviar = () => backend(path, { method: metodo, headers: { Authorization: `Bearer ${access}` }, ...(metodo === "POST" ? { body: JSON.stringify(dados ?? {}) } : {}) });
    let result = access ? await enviar() : null;
    if ((!result || result.status === 401) && refresh) {
      const renewed = await refreshOnce(refresh);
      if (renewed.tokens) { tokens = renewed.tokens; access = tokens.access; result = await enviar(); }
      else if (renewed.status !== 401 && renewed.status !== 403) return NextResponse.json({ mensagem: "Não foi possível renovar a sessão." }, { status: 503 });
    }
    if (!result || result.status === 401) { const response = NextResponse.json({ mensagem: "Sessão encerrada." }, { status: 401 }); clearTokens(response); return response; }
    const response = NextResponse.json(await result.json(), { status: result.status });
    if (tokens) setTokens(response, tokens);
    return response;
  } catch {
    const response = NextResponse.json({ mensagem: "Não foi possível conectar. Consulte o estado antes de reenviar." }, { status: 503 });
    if (tokens) setTokens(response, tokens);
    return response;
  }
}
