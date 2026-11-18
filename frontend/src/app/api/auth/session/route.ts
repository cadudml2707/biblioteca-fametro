import { NextRequest, NextResponse } from "next/server";
import { clearTokens, identity, refreshOnce, sameOrigin, setTokens } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  const access = request.cookies.get("bf_access")?.value;
  const refresh = request.cookies.get("bf_refresh")?.value;
  const denied = () => { const response = NextResponse.json({ mensagem: "Sessão encerrada." }, { status: 401 }); clearTokens(response); return response; };
  try {
    if (access) {
      const current = await identity(access);
      if (current.user) return NextResponse.json({ usuario: current.user });
      if (current.response.status !== 401 && current.response.status !== 403) return NextResponse.json({ mensagem: "Não foi possível consultar a sessão." }, { status: 503 });
    }
    if (!refresh) return denied();
    const renewed = await refreshOnce(refresh);
    if (!renewed.tokens) {
      if (renewed.status === 401 || renewed.status === 403) return denied();
      return NextResponse.json({ mensagem: "Não foi possível renovar a sessão." }, { status: 503 });
    }
    const response = NextResponse.json({ renovada: true });
    // Preserve rotated tokens even if identity is temporarily unavailable.
    setTokens(response, renewed.tokens);
    return response;
  } catch {
    return NextResponse.json({ mensagem: "Não foi possível conectar ao servidor. Tente novamente." }, { status: 503 });
  }
}
