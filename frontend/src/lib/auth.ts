export type User = { id: number; nome: string; email: string; perfil: number };
export async function session(): Promise<User | null> {
  const response = await fetch("/api/auth/session", { method: "POST" });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error("Não foi possível conectar ao servidor. Tente novamente.");
  const data = await response.json();
  if (data.renovada) {
    const next = await fetch("/api/auth/session", { method: "POST" });
    if (next.status === 401) return null;
    if (!next.ok) throw new Error("Não foi possível consultar a sessão. Tente novamente.");
    return (await next.json()).usuario;
  }
  return data.usuario;
}
let pending: Promise<User | null> | undefined;
export function sharedSession() {
  if (!pending) pending = session().finally(() => { pending = undefined; });
  return pending;
}
