"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { operacao, todasPaginas, type Aluno, type Obra, type Exemplar, type Reserva, type Emprestimo } from "@/lib/api/circulacao";

const dataHora = (valor: string | null) => valor ? new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Manaus", dateStyle: "short", timeStyle: "short" }).format(new Date(valor)) : "—";
const dataDia = (valor: string | null) => valor ? valor.split("-").reverse().join("/") : "—";

export function GestaoCirculacao({ tela }: { tela: "reservas" | "circulacao" }) {
  const [alunos, setAlunos] = useState<Aluno[]>([]);
  const [obras, setObras] = useState<Obra[]>([]);
  const [exemplares, setExemplares] = useState<Exemplar[]>([]);
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [emprestimos, setEmprestimos] = useState<Emprestimo[]>([]);
  const [filtros, setFiltros] = useState({ usuario_id: "", obra_id: "", exemplar_id: "", situacao: "" });
  const [carregando, setCarregando] = useState(true);
  const [ocupado, setOcupado] = useState(false);
  const [erroCarga, setErroCarga] = useState(false);
  const [mensagem, setMensagem] = useState("");
  const [dialogo, setDialogo] = useState<"retirada" | "devolucao" | null>(null);
  const [selecionado, setSelecionado] = useState<Emprestimo | null>(null);
  const [dados, setDados] = useState({ usuario_id: "", exemplar_id: "", reserva_id: "" });
  const [erros, setErros] = useState<Record<string, string[]>>({});
  const dialogRef = useRef<HTMLDialogElement>(null);

  const carregar = useCallback(async () => {
    setCarregando(true); setErroCarga(false);
    try {
      const [alunosApi, obrasApi, exemplaresApi, reservasApi, emprestimosApi] = await Promise.all([
        todasPaginas<Aluno>("alunos"), todasPaginas<Obra>("obras"), operacao<Exemplar[]>("exemplares"), operacao<Reserva[]>("reservas"), operacao<Emprestimo[]>("emprestimos"),
      ]);
      setAlunos(alunosApi); setObras(obrasApi); setExemplares(exemplaresApi); setReservas(reservasApi); setEmprestimos(emprestimosApi);
    } catch (erro) { setErroCarga(true); setMensagem(erro instanceof Error ? erro.message : "Não foi possível carregar os dados."); }
    finally { setCarregando(false); }
  }, []);
  useEffect(() => { void carregar(); }, [carregar]);
  useEffect(() => { if (dialogo && dialogRef.current && !dialogRef.current.open) dialogRef.current.showModal(); }, [dialogo]);
  const atualiza = (campo: string, valor: string) => setFiltros(anterior => ({ ...anterior, [campo]: valor }));
  const limparErro = () => { setMensagem(""); setErros({}); };
  const abrirRetirada = () => { limparErro(); setDados({ usuario_id: "", exemplar_id: "", reserva_id: "" }); setDialogo("retirada"); };
  const fechar = () => { if (!ocupado) { setDialogo(null); limparErro(); } };
  async function executar(recurso: "reservas" | "emprestimos", id: number, acao: string) {
    if (ocupado) return; setOcupado(true); limparErro();
    try { await operacao(recurso, { metodo: "POST", id, acao }); setDialogo(null); await carregar(); setMensagem(acao === "devolver" ? "Devolução registrada." : acao === "confirmar" ? "Reserva confirmada." : "Reserva cancelada."); }
    catch (erro) { setMensagem(erro instanceof Error ? erro.message : "Não foi possível concluir a operação."); }
    finally { setOcupado(false); }
  }
  async function retirar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (ocupado) return; setOcupado(true); limparErro();
    try {
      const resultado = await operacao<Emprestimo>("emprestimos", { metodo: "POST", dados: { usuario_id: Number(dados.usuario_id), exemplar_id: Number(dados.exemplar_id), reserva_id: dados.reserva_id ? Number(dados.reserva_id) : null } });
      setDialogo(null); await carregar(); setMensagem(`Retirada registrada. Devolução prevista para ${dataDia(resultado.data_prevista)}.`);
    } catch (erro) {
      setMensagem(erro instanceof Error ? erro.message : "Não foi possível registrar a retirada.");
      if (typeof erro === "object" && erro && "detalhe" in erro) setErros((erro as { detalhe: { erros?: Record<string, string[]> } }).detalhe.erros ?? {});
    } finally { setOcupado(false); }
  }
  const exemplaresDisponiveis = exemplares.filter(e => e.is_active && e.situacao === 1 && obras.some(o => o.id === e.obra_id && o.is_active));
  const reservasDisponiveis = reservas.filter(r => r.is_active && r.situacao === 2);
  const reservasFiltradas = reservas.filter(r => (!filtros.usuario_id || String(r.usuario_id) === filtros.usuario_id) && (!filtros.obra_id || String(r.obra_id) === filtros.obra_id) && (!filtros.situacao || String(r.situacao) === filtros.situacao));
  const emprestimosFiltrados = emprestimos.filter(e => (!filtros.usuario_id || String(e.usuario_id) === filtros.usuario_id) && (!filtros.exemplar_id || String(e.exemplar_id) === filtros.exemplar_id) && (!filtros.situacao || (e.is_active ? "ativo" : "devolvido") === filtros.situacao));

  return <section className="cadastros">
    <div className="cadastros-heading"><h1>{tela === "reservas" ? "Reservas" : "Circulação"}</h1>{tela === "circulacao" && !erroCarga && <button className="primary-button" onClick={abrirRetirada}>Nova retirada</button>}</div>
    {mensagem && !dialogo && <p role="status" className="cadastros-message">{mensagem}</p>}
    {carregando ? <p role="status">Carregando...</p> : erroCarga ? <button type="button" onClick={() => void carregar()}>Tentar novamente</button> : <>
      <div className="circulacao-filtros">
        <label>Aluno<select value={filtros.usuario_id} onChange={e => atualiza("usuario_id", e.target.value)}><option value="">Todos</option>{alunos.map(a => <option key={a.id} value={a.id}>{a.nome} — {a.email}{!a.is_active ? " (inativo)" : ""}</option>)}</select></label>
        {tela === "reservas" ? <label>Obra<select value={filtros.obra_id} onChange={e => atualiza("obra_id", e.target.value)}><option value="">Todas</option>{obras.map(o => <option key={o.id} value={o.id}>{o.titulo}</option>)}</select></label> : <label>Exemplar<select value={filtros.exemplar_id} onChange={e => atualiza("exemplar_id", e.target.value)}><option value="">Todos</option>{exemplares.map(e => <option key={e.id} value={e.id}>{e.codigo}</option>)}</select></label>}
        <label>Situação<select value={filtros.situacao} onChange={e => atualiza("situacao", e.target.value)}><option value="">Todas</option>{tela === "reservas" ? <><option value="1">Solicitada</option><option value="2">Confirmada</option><option value="3">Atendida</option><option value="4">Cancelada</option></> : <><option value="ativo">Ativo</option><option value="devolvido">Devolvido</option></>}</select></label>
      </div>
      {tela === "reservas" ? reservasFiltradas.length === 0 ? <p>Nenhuma reserva encontrada.</p> : <div className="catalog-table"><table><thead><tr><th>Aluno</th><th>Obra</th><th>Situação</th><th>Solicitada em</th><th>Confirmada em</th><th>Limite de retirada</th><th>Encerrada em</th><th>Ações</th></tr></thead><tbody>{reservasFiltradas.map(r => <tr key={r.id}><td>{r.aluno.nome}<br /><small>{r.aluno.email}</small></td><td>{r.obra.titulo}</td><td>{r.situacao_descricao}</td><td>{dataHora(r.data_reserva)}</td><td>{dataHora(r.confirmada_em)}</td><td>{dataHora(r.data_limite)}</td><td>{dataHora(r.encerrada_em)}</td><td><div className="cadastros-actions">{r.is_active && r.situacao === 1 && <button disabled={ocupado} onClick={() => void executar("reservas", r.id, "confirmar")}>Confirmar</button>}{r.is_active && [1, 2].includes(r.situacao) && <button disabled={ocupado} onClick={() => void executar("reservas", r.id, "cancelar")}>Cancelar</button>}</div></td></tr>)}</tbody></table></div> : emprestimosFiltrados.length === 0 ? <p>Nenhum empréstimo encontrado.</p> : <div className="catalog-table"><table><thead><tr><th>Aluno</th><th>Obra / exemplar</th><th>Situação</th><th>Retirada</th><th>Previsão</th><th>Devolução</th><th>Ações</th></tr></thead><tbody>{emprestimosFiltrados.map(e => <tr key={e.id}><td>{e.aluno.nome}<br /><small>{e.aluno.email}</small></td><td>{e.exemplar.obra_titulo}<br /><small>{e.exemplar.codigo}</small></td><td><span className={`cadastros-status ${e.is_active ? "cadastros-status-ativo" : "cadastros-status-inativo"}`}>{e.is_active ? "Ativo" : "Devolvido"}</span></td><td>{dataHora(e.data_retirada)}</td><td>{dataDia(e.data_prevista)}</td><td>{dataHora(e.data_devolucao)}</td><td><div className="cadastros-actions">{e.is_active && <button disabled={ocupado} onClick={() => { limparErro(); setSelecionado(e); setDialogo("devolucao"); }}>Devolver</button>}</div></td></tr>)}</tbody></table></div>}
    </>}
    {dialogo && <dialog ref={dialogRef} className="cadastros-dialog" aria-labelledby="titulo-circulacao" onCancel={e => { if (ocupado) e.preventDefault(); }} onClose={() => setDialogo(null)}>
      {dialogo === "retirada" ? <form className="cadastros-form cadastros-dialog-form" onSubmit={retirar}>
        <h2 id="titulo-circulacao">Nova retirada</h2>{mensagem && <p role="alert">{mensagem}</p>}
        <div className="cadastros-field"><label htmlFor="reserva-retirada">Reserva confirmada (opcional)</label><select id="reserva-retirada" value={dados.reserva_id ? `${dados.reserva_id}:${dados.exemplar_id}` : ""} onChange={e => { const [reservaId, exemplarId] = e.target.value.split(":"); const reserva = reservasDisponiveis.find(r => String(r.id) === reservaId); setDados(reserva ? { usuario_id: String(reserva.usuario_id), exemplar_id: exemplarId, reserva_id: reservaId } : { usuario_id: "", exemplar_id: "", reserva_id: "" }); limparErro(); }}><option value="">Sem reserva</option>{reservasDisponiveis.flatMap(r => { const disponiveis = exemplaresDisponiveis.filter(e => e.obra_id === r.obra_id); const alunoAtivo = alunos.some(a => a.id === r.usuario_id && a.is_active); if (!disponiveis.length || !alunoAtivo) return [<option key={r.id} value={`indisponivel-${r.id}`} disabled>{r.aluno.nome} — {r.obra.titulo} ({alunoAtivo ? "sem exemplar disponível" : "aluno inativo"})</option>]; return disponiveis.map(exemplar => <option key={`${r.id}:${exemplar.id}`} value={`${r.id}:${exemplar.id}`}>{r.aluno.nome} — {r.obra.titulo} — {exemplar.codigo}</option>); })}</select>{erros.reserva_id && <p role="alert" className="cadastros-error">{erros.reserva_id.join(" ")}</p>}</div>
        <div className="cadastros-field"><label htmlFor="aluno-retirada">Aluno</label><select id="aluno-retirada" required disabled={Boolean(dados.reserva_id)} value={dados.usuario_id} onChange={e => setDados({ ...dados, usuario_id: e.target.value })}><option value="">Selecione</option>{alunos.filter(a => a.is_active).map(a => <option value={a.id} key={a.id}>{a.nome} — {a.email}</option>)}</select>{erros.usuario_id && <p role="alert" className="cadastros-error">{erros.usuario_id.join(" ")}</p>}</div>
        <div className="cadastros-field"><label htmlFor="exemplar-retirada">Exemplar disponível</label><select id="exemplar-retirada" required disabled={Boolean(dados.reserva_id)} value={dados.exemplar_id} onChange={e => setDados({ ...dados, exemplar_id: e.target.value })}><option value="">Selecione</option>{exemplaresDisponiveis.map(e => <option key={e.id} value={e.id}>{obras.find(o => o.id === e.obra_id)?.titulo} — {e.codigo}</option>)}</select>{erros.exemplar_id && <p role="alert" className="cadastros-error">{erros.exemplar_id.join(" ")}</p>}</div>
        <div className="cadastros-actions"><button className="primary-button" disabled={ocupado}>{ocupado ? "Salvando..." : "Registrar retirada"}</button><button type="button" disabled={ocupado} onClick={fechar}>Cancelar</button></div>
      </form> : <div className="cadastros-form cadastros-dialog-form"><h2 id="titulo-circulacao">Confirmar devolução</h2><p>Confirmar a devolução de {selecionado?.exemplar.obra_titulo} ({selecionado?.exemplar.codigo}) por {selecionado?.aluno.nome}?</p>{mensagem && <p role="alert">{mensagem}</p>}<div className="cadastros-actions"><button className="primary-button" disabled={ocupado} onClick={() => selecionado && void executar("emprestimos", selecionado.id, "devolver")}>Confirmar devolução</button><button type="button" disabled={ocupado} onClick={fechar}>Cancelar</button></div></div>}
    </dialog>}
  </section>;
}
