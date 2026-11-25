import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

const CAMPOS = new Set([
  "limite_reservas_ativas",
  "limite_emprestimos_ativos",
  "prazo_emprestimo_dias",
  "prazo_retirada_reserva_dias",
]);

type Entrada = { metodo?: string; dados?: unknown };

function dadosValidos(value: unknown): value is Record<string, number> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const entries = Object.entries(value);
  return entries.length > 0 && entries.every(([campo, numero]) =>
    CAMPOS.has(campo) && Number.isSafeInteger(numero) && (numero as number) >= 1,
  );
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });

  let corpo: unknown;
  try { corpo = await request.json(); } catch { return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 }); }
  if (!corpo || typeof corpo !== "object" || Array.isArray(corpo)) return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 });
  const entrada = corpo as Entrada;
  const metodo = entrada.metodo;
  if (!["GET", "POST", "PATCH"].includes(metodo ?? "")) return NextResponse.json({ mensagem: "Operação inválida." }, { status: 400 });
  if ((metodo === "GET" && entrada.dados !== undefined) || (metodo !== "GET" && !dadosValidos(entrada.dados))) {
    return NextResponse.json({ mensagem: "Dados inválidos." }, { status: 400 });
  }

  const refresh = request.cookies.get("bf_refresh")?.value;
  let access = request.cookies.get("bf_access")?.value;
  let tokens: { access: string; refresh: string } | undefined;
  const enviar = () => backend("/configuracao-biblioteca", {
    method: metodo,
    headers: { Authorization: `Bearer ${access}` },
    ...(metodo !== "GET" ? { body: JSON.stringify(entrada.dados) } : {}),
  });

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
