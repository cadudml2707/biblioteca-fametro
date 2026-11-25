import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

type Entrada = { data_inicio?: unknown; data_fim?: unknown };
const formatoData = /^\d{4}-\d{2}-\d{2}$/;

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  let corpo: unknown;
  try { corpo = await request.json(); } catch { return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 }); }
  if (!corpo || typeof corpo !== "object" || Array.isArray(corpo)) return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 });
  const entrada = corpo as Entrada;
  if (typeof entrada.data_inicio !== "string" || !formatoData.test(entrada.data_inicio)
    || typeof entrada.data_fim !== "string" || !formatoData.test(entrada.data_fim)) {
    return NextResponse.json({ mensagem: "Informe um período válido." }, { status: 400 });
  }

  const params = new URLSearchParams({ data_inicio: entrada.data_inicio, data_fim: entrada.data_fim });
  const path = `/relatorios?${params}`;
  const refresh = request.cookies.get("bf_refresh")?.value;
  let access = request.cookies.get("bf_access")?.value;
  let tokens: { access: string; refresh: string } | undefined;
  const enviar = () => backend(path, { headers: { Authorization: `Bearer ${access}` } });

  try {
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
    const response = NextResponse.json({ mensagem: "Não foi possível conectar ao servidor." }, { status: 503 });
    if (tokens) setTokens(response, tokens);
    return response;
  }
}
