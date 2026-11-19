import { consultarApi } from "./cliente";

export type Obra = { id: number; titulo: string; autor: string; isbn: string | null; quantidade_disponivel: number };
export type Pagina<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export function consultarObras(search: string, page: number): Promise<Pagina<Obra>> {
  const params = new URLSearchParams({ search, page: String(page) });
  return consultarApi<Pagina<Obra>>(`/api/obras?${params}`);
}
