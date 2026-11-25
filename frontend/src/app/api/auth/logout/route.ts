import { NextRequest, NextResponse } from "next/server";
import { backend, clearTokens, refreshOnce, sameOrigin } from "@/lib/server-auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ mensagem: "Origem não permitida." }, { status: 403 });
  let access = request.cookies.get("bf_access")?.value;
  let refresh = request.cookies.get("bf_refresh")?.value;
  let revogado = !refresh;
  try {
    if (!access && refresh) {
      const renewed = await refreshOnce(refresh);
      if (renewed.tokens) { access = renewed.tokens.access; refresh = renewed.tokens.refresh; }
      else if (renewed.status === 401 || renewed.status === 403) revogado = true;
    }
    if (access && refresh) {
      const result = await backend("/logout", { method: "POST", headers: { Authorization: `Bearer ${access}` }, body: JSON.stringify({ refresh }) });
      revogado = result.ok || result.status === 401;
    }
  } catch { /* A sessão local ainda será encerrada. */ }
  const response = NextResponse.json({ revogado });
  clearTokens(response);
  return response;
}
