import { FalhaApi, type ErroApi } from "./cliente";

export type Aluno = { id: number; nome: string; email: string; is_active: boolean };
export type Obra = { id: number; titulo: string; is_active: boolean };
export type Exemplar = { id: number; codigo: string; obra_id: number; situacao: number; is_active: boolean };
export type Reserva = { id: number; usuario_id: number; obra_id: number; aluno: Aluno; obra: Obra; situacao: number; situacao_descricao: string; is_active: boolean; data_reserva: string; confirmada_em: string | null; data_limite: string | null; encerrada_em: string | null };
export type Emprestimo = { id: number; usuario_id: number; exemplar_id: number; aluno: Aluno; exemplar: { codigo: string; obra_titulo: string }; is_active: boolean; data_retirada: string; data_prevista: string; data_devolucao: string | null };
export type Pagina<T> = { results: T[]; next: string | null };
type Recurso = "alunos" | "obras" | "exemplares" | "reservas" | "emprestimos";
export async function operacao<T>(recurso: Recurso, opcoes: { metodo?: "GET" | "POST"; id?: number; acao?: string; filtros?: Record<string, string>; dados?: Record<string, number | null> } = {}): Promise<T> {
  let response: Response;
  try { response = await fetch("/api/circulacao", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ recurso, metodo: "GET", ...opcoes }) }); }
  catch { throw new Error("Falha de conexão. Consulte o estado antes de reenviar a operação."); }
  if (response.status === 401) { window.location.assign("/login"); throw new Error("Sessão encerrada."); }
  if (!response.ok) { const erro = await response.json() as ErroApi; const mensagem = erro.mensagem || "Não foi possível concluir a operação."; throw new FalhaApi(response.status, { ...erro, mensagem: erro.codigo === "configuracao_ausente" ? `${mensagem} Solicite ao administrador a configuração da biblioteca.` : mensagem }); }
  return response.json();
}
export async function todasPaginas<T>(recurso: "alunos" | "obras", search = ""): Promise<T[]> {
  const items: T[] = []; let page = 1; let next: string | null;
  do { const resposta: Pagina<T> = await operacao(recurso, { filtros: { page: String(page++), search } }); items.push(...resposta.results); next = resposta.next; } while (next);
  return items;
}
