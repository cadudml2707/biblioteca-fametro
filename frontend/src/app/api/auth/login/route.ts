import { NextRequest, NextResponse } from "next/server";
import { backend, sameOrigin, setTokens } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  try {
    const { email, password } = await request.json();
    const result = await backend("/login", { method: "POST", body: JSON.stringify({ email, password, plataforma: "web" }) });
    const data = await result.json();
    if (!result.ok) return NextResponse.json(data, { status: result.status });
    const response = NextResponse.json({ usuario: data.usuario });
    setTokens(response, data);
    return response;
  } catch {
    return NextResponse.json({ mensagem: "Não foi possível conectar ao servidor. Tente novamente." }, { status: 503 });
  }
}
