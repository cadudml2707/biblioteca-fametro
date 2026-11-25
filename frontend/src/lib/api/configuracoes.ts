import { FalhaApi, type ErroApi } from "./cliente";

export type Configuracao = {
  id: number;
  limite_reservas_ativas: number;
  limite_emprestimos_ativos: number;
  prazo_emprestimo_dias: number;
  prazo_retirada_reserva_dias: number;
  is_active: boolean;
};

export type Parametros = Omit<Configuracao, "id" | "is_active">;
export type MetodoConfiguracao = "GET" | "POST" | "PATCH";

export async function requisitarConfiguracao<T>(metodo: MetodoConfiguracao, dados?: Parametros): Promise<T> {
  let response: Response;
  try {
    response = await fetch("/api/configuracoes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ metodo, ...(dados ? { dados } : {}) }),
    });
  } catch {
    throw new Error("Falha de conexão. Tente novamente.");
  }

  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("Sessão encerrada.");
  }
  if (!response.ok) {
    const detalhe = await response.json() as ErroApi;
    throw new FalhaApi(response.status, {
      ...detalhe,
      mensagem: detalhe.mensagem || "Não foi possível concluir a operação.",
    });
  }
  return response.json();
}
