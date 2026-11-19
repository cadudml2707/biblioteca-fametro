import { FalhaApi, type ErroApi } from "./cliente";

export type Recurso = "obras" | "exemplares" | "usuarios";
export async function requisitar<T>(recurso: Recurso, metodo: "GET" | "POST" | "PATCH", opcoes: {
  id?: number; dados?: Record<string, unknown>; search?: string; page?: number;
} = {}): Promise<T> {
  const response = await fetch(`/api/cadastros/${recurso}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ metodo, ...opcoes }),
  });
  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("Sessão encerrada.");
  }
  if (!response.ok) {
    const detalhe = await response.json() as ErroApi;
    throw new FalhaApi(response.status, { ...detalhe, mensagem: detalhe.mensagem || "Não foi possível concluir a operação." });
  }
  return response.json();
}

export type ObraCadastro = { id: number; titulo: string; autor: string; isbn: string | null; editora: string | null; ano_publicacao: number | null; quantidade_disponivel: number; is_active: boolean };
export type Exemplar = { id: number; obra_id: number; codigo: string; situacao: number; is_active: boolean };
export type UsuarioCadastro = { id: number; nome: string; email: string; perfil: number; is_active: boolean };
export type Pagina<T> = { count: number; next: string | null; previous: string | null; results: T[] };
