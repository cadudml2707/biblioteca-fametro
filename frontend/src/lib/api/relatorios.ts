import { FalhaApi, type ErroApi } from "./cliente";

export type PeriodoRelatorio = { data_inicio: string; data_fim: string };
export type TotalSituacaoReserva = { situacao: number; descricao: string; total: number };
export type RelatorioResumo = {
  periodo: PeriodoRelatorio;
  acervo: {
    obras_ativas: number;
    exemplares_ativos: number;
    exemplares_disponiveis: number;
    exemplares_emprestados: number;
  };
  emprestimos: {
    ativos: number;
    atrasados: number;
    retiradas_periodo: number;
    devolucoes_periodo: number;
  };
  reservas: { total_periodo: number; por_situacao: TotalSituacaoReserva[] };
};

export async function consultarRelatorio(periodo: PeriodoRelatorio, signal?: AbortSignal): Promise<RelatorioResumo> {
  let response: Response;
  try {
    response = await fetch("/api/relatorios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(periodo),
      signal,
    });
  } catch (erro) {
    if (erro instanceof DOMException && erro.name === "AbortError") throw erro;
    throw new Error("Falha de conexão. Tente novamente.");
  }
  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("Sessão encerrada.");
  }
  if (!response.ok) {
    const detalhe = await response.json() as ErroApi;
    throw new FalhaApi(response.status, { ...detalhe, mensagem: detalhe.mensagem || "Não foi possível carregar os relatórios." });
  }
  return response.json();
}
