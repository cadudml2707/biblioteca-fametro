"use client";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { sharedSession, type User } from "@/lib/auth";
import { Brand } from "@/components/brand";
import { BookOpen, Bookmark, LogOut, Search, ArrowLeft, ArrowRight, RefreshCw, LibraryBig } from "lucide-react";

type Obra = { id: number; titulo: string; autor: string; isbn: string; editora: string; ano_publicacao: number; quantidade_disponivel: number; pode_solicitar_reserva?: boolean };
type Reserva = { id: number; obra: Obra; situacao_descricao: string; data_reserva: string; data_limite: string | null };
async function api(body: object) {
  const response = await fetch("/api/aluno", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.mensagem || "Não foi possível concluir a operação.");
  return data;
}
export default function AlunoPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [tab, setTab] = useState<"catalogo" | "reservas">("catalogo");
  const [search, setSearch] = useState(""); const [query, setQuery] = useState(""); const [page, setPage] = useState(1);
  const [obras, setObras] = useState<Obra[]>([]); const [next, setNext] = useState(false);
  const [reservas, setReservas] = useState<Reserva[]>([]); const [detail, setDetail] = useState<Obra | null>(null);
  const [loading, setLoading] = useState(false); const [sending, setSending] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  useEffect(() => { sharedSession().then(u => { if (!u) router.replace("/login"); else if (u.perfil !== 1) router.replace("/gestao"); else setUser(u); }).catch(() => setError("Não foi possível consultar a sessão. Atualize a página para tentar novamente.")); }, [router]);
  const load = useCallback(async () => {
    if (!user) return; setLoading(true); setError("");
    try { const data = await api(tab === "catalogo" ? { action: "catalogo", search: query, page } : { action: "reservas" }); if (tab === "catalogo") { setObras(data.results ?? data); setNext(Boolean(data.next)); } else setReservas(data.results ?? data); }
    catch (e) { setError(e instanceof Error ? e.message : "Erro ao carregar."); } finally { setLoading(false); }
  }, [user, tab, query, page]);
  useEffect(() => { void load(); }, [load]);
  async function open(id: number) { setLoading(true); setError(""); try { setDetail(await api({ action: "detalhe", id })); } catch (e) { setError(e instanceof Error ? e.message : "Erro ao carregar."); } finally { setLoading(false); } }
  async function reserve() { if (!detail || sending) return; setSending(true); setError(""); setNotice(""); try { await api({ action: "reservar", id: detail.id }); setNotice("Reserva solicitada com sucesso."); setDetail(await api({ action: "detalhe", id: detail.id })); } catch (e) { setError(e instanceof Error ? e.message : "Erro ao reservar."); } finally { setSending(false); } }
  async function logout() { try { await fetch("/api/auth/logout", { method: "POST" }); router.replace("/login"); } catch { setError("Não foi possível sair. Tente novamente."); } }
  if (!user) return <main className="aluno-shell"><p role="status">{error || "Carregando sessão..."}</p></main>;
  return <div className="aluno-app">
    <a className="skip-link" href="#aluno-conteudo">Pular para o conteúdo</a>
    <aside className="aluno-sidebar"><div className="aluno-brand"><Brand /></div><span className="aluno-nav-label">ÁREA DO ALUNO</span>
      <nav className="aluno-nav" aria-label="Área do aluno">
        <button aria-current={tab === "catalogo" ? "page" : undefined} onClick={() => { setTab("catalogo"); setDetail(null); setNotice(""); }}><BookOpen size={19}/> Catálogo</button>
        <button aria-current={tab === "reservas" ? "page" : undefined} onClick={() => { setTab("reservas"); setDetail(null); setNotice(""); }}><Bookmark size={19}/> Minhas reservas</button>
      </nav><button className="aluno-logout" onClick={logout}><LogOut size={18}/> Sair da conta</button>
    </aside>
    <div className="aluno-main"><header className="aluno-header"><strong>Biblioteca</strong><div className="aluno-account"><div><strong>{user.nome}</strong><span>Aluno</span></div><span className="avatar" aria-hidden="true">{user.nome.trim().slice(0, 1).toUpperCase()}</span></div></header>
    <main className="aluno-content" id="aluno-conteudo">
    {error && <div className="aluno-alert" role="alert">{error} <button onClick={() => void load()}>Atualizar</button></div>}{notice && <div className="aluno-success" role="status">{notice}</div>}
    {detail ? <section className="aluno-detail"><button className="aluno-back" onClick={() => setDetail(null)}><ArrowLeft size={18}/> Voltar ao catálogo</button><div className="aluno-detail-card"><div className="aluno-book-icon"><BookOpen size={30}/></div><div><span className="aluno-eyebrow">DETALHES DA OBRA</span><h1>{detail.titulo}</h1><p className="aluno-detail-author">{detail.autor}</p><dl className="aluno-meta"><div><dt>Editora</dt><dd>{detail.editora || "Não informada"}</dd></div><div><dt>ISBN</dt><dd>{detail.isbn || "Não informado"}</dd></div><div><dt>Disponibilidade</dt><dd>{detail.quantidade_disponivel} {detail.quantidade_disponivel === 1 ? "exemplar disponível" : "exemplares disponíveis"}</dd></div></dl><button className="primary-button aluno-reserve" disabled={!detail.pode_solicitar_reserva || sending} onClick={() => void reserve()}>{sending ? "Enviando..." : "Solicitar reserva"}<ArrowRight size={18}/></button>{!detail.pode_solicitar_reserva && <p className="aluno-hint">A solicitação de reserva não está disponível para esta obra.</p>}</div></div></section> : tab === "catalogo" ? <section>
      <div className="aluno-welcome"><div><span>ÁREA DO ALUNO</span><h1>Olá, {user.nome.trim().split(/\s+/)[0]}!</h1><p>Explore o acervo e encontre sua próxima leitura.</p></div><LibraryBig className="aluno-welcome-icon" size={96} strokeWidth={1}/></div>
      <div className="aluno-section-heading"><div><h2>Catálogo de obras</h2><p>Pesquise e consulte a disponibilidade dos livros.</p></div></div>
      <form className="aluno-search" onSubmit={(e: FormEvent) => { e.preventDefault(); setPage(1); setQuery(search); }}><label htmlFor="busca">Buscar no catálogo</label><div><Search size={19} aria-hidden="true"/><input id="busca" placeholder="Título, autor ou ISBN" value={search} onChange={e => setSearch(e.target.value)} /><button type="submit">Buscar</button></div></form>
      {loading ? <p className="aluno-empty" role="status">Carregando obras...</p> : obras.length ? <div className="aluno-list">{obras.map(o => <article className="aluno-card" key={o.id}><div className="aluno-card-icon"><BookOpen size={21}/></div><div className="aluno-card-body"><h3>{o.titulo}</h3><p>{o.autor}</p><span className="aluno-availability">{o.quantidade_disponivel} {o.quantidade_disponivel === 1 ? "exemplar disponível" : "exemplares disponíveis"}</span></div><button className="aluno-card-action" onClick={() => void open(o.id)}>Ver detalhes <ArrowRight size={17}/></button></article>)}</div> : <p className="aluno-empty">Nenhuma obra encontrada.</p>}
      <div className="aluno-pages"><button disabled={page === 1 || loading} onClick={() => setPage(page - 1)}>Anterior</button><span>Página {page}</span><button disabled={!next || loading} onClick={() => setPage(page + 1)}>Próxima</button></div>
    </section> : <section><div className="aluno-section-heading aluno-reservas-heading"><div><h1>Minhas reservas</h1><p>Acompanhe suas solicitações e os prazos de retirada.</p></div><button className="aluno-refresh" onClick={() => void load()} disabled={loading}><RefreshCw size={17}/> Atualizar</button></div>
      {loading ? <p className="aluno-empty" role="status">Carregando reservas...</p> : reservas.length ? <div className="aluno-list">{reservas.map(r => <article className="aluno-card" key={r.id}><div className="aluno-card-icon"><Bookmark size={21}/></div><div className="aluno-card-body"><h3>{r.obra.titulo}</h3><p>{r.obra.autor}</p><span className="aluno-status">{r.situacao_descricao}</span><p className="aluno-dates">Solicitada em {new Date(r.data_reserva).toLocaleDateString("pt-BR", { timeZone: "America/Manaus" })}{r.data_limite && <> · Prazo: {new Date(r.data_limite).toLocaleDateString("pt-BR", { timeZone: "America/Manaus" })}</>}</p></div></article>)}</div> : <p className="aluno-empty">Você ainda não tem reservas.</p>}</section>}
    </main></div></div>;
}
