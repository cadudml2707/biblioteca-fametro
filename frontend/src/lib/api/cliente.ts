export type ErroApi = { codigo?: string; mensagem: string; erros?: Record<string, string[]> };

export class FalhaApi extends Error {
  constructor(public status: number, public detalhe: ErroApi) {
    super(detalhe.mensagem);
  }
}

export async function consultarApi<T>(url: string): Promise<T> {
  const response = await fetch(url, { method: "POST" });
  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("Sessão encerrada.");
  }
  if (!response.ok) {
    const erro = await response.json() as ErroApi;
    throw new FalhaApi(response.status, { ...erro, mensagem: erro.mensagem || "Não foi possível consultar os dados." });
  }
  return response.json();
}
