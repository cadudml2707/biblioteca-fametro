"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FalhaApi } from "@/lib/api/cliente";
import { requisitar, type Recurso, type Pagina, type ObraCadastro } from "@/lib/api/cadastros";

type Registro = { id: number; is_active: boolean; [campo: string]: unknown };
type Campo = { nome: string; rotulo: string; tipo?: string; obrigatorio?: boolean };
const campos: Record<Recurso, Campo[]> = {
  obras: [
    { nome: "titulo", rotulo: "Título", obrigatorio: true }, { nome: "autor", rotulo: "Autor", obrigatorio: true },
    { nome: "isbn", rotulo: "ISBN" }, { nome: "editora", rotulo: "Editora" },
    { nome: "ano_publicacao", rotulo: "Ano de publicação", tipo: "number" },
  ],
  exemplares: [{ nome: "obra_id", rotulo: "Obra", obrigatorio: true }, { nome: "codigo", rotulo: "Código", obrigatorio: true }],
  usuarios: [
    { nome: "nome", rotulo: "Nome", obrigatorio: true }, { nome: "email", rotulo: "E-mail", tipo: "email", obrigatorio: true },
    { nome: "perfil", rotulo: "Perfil", obrigatorio: true }, { nome: "password", rotulo: "Senha", tipo: "password" },
  ],
};
const titulos: Record<Recurso, string> = { obras: "Obras", exemplares: "Exemplares", usuarios: "Usuários" };

export function Cadastros({ recurso }: { recurso: Recurso }) {
  const [registros, setRegistros] = useState<Registro[]>([]);
  const [obras, setObras] = useState<ObraCadastro[]>([]);
  const [pagina, setPagina] = useState(1);
  const [paginacao, setPaginacao] = useState<Pagina<Registro> | null>(null);
  const [busca, setBusca] = useState("");
  const [termo, setTermo] = useState("");
  const [detalhe, setDetalhe] = useState<Registro | null>(null);
  const [editando, setEditando] = useState<Registro | null | undefined>(undefined);
  const [valores, setValores] = useState<Record<string, string>>({});
  const [erros, setErros] = useState<Record<string, string[]>>({});
  const [mensagem, setMensagem] = useState("");
  const [acessoNegado, setAcessoNegado] = useState(false);
  const [falhaLista, setFalhaLista] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (editando !== undefined && dialog && !dialog.open) dialog.showModal();
  }, [editando]);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setFalhaLista(false);
    try {
      if (recurso === "obras") {
        const resultado = await requisitar<Pagina<Registro>>(recurso, "GET", { page: pagina, search: termo });
        setRegistros(resultado.results); setPaginacao(resultado);
      } else {
        setRegistros(await requisitar<Registro[]>(recurso, "GET"));
        if (recurso === "exemplares") {
          const todas: ObraCadastro[] = [];
          let numero = 1;
          let proxima: string | null;
          do {
            const resultado: Pagina<ObraCadastro> = await requisitar("obras", "GET", { page: numero });
            todas.push(...resultado.results);
            proxima = resultado.next;
            numero += 1;
          } while (proxima);
          setObras(todas);
        }
      }
    } catch (erro) { setFalhaLista(true); setAcessoNegado(erro instanceof FalhaApi && erro.status === 403); setMensagem(erro instanceof Error ? erro.message : "Não foi possível carregar."); }
    finally { setCarregando(false); }
  }, [recurso, pagina, termo]);

  useEffect(() => { void carregar(); }, [carregar]);

  function abrir(registro: Registro | null) {
    const inicial: Record<string, string> = {};
    for (const campo of campos[recurso]) inicial[campo.nome] = campo.nome === "password" ? "" : String(registro?.[campo.nome] ?? "");
    setValores(inicial); setErros({}); setMensagem(""); setEditando(registro);
  }

  async function salvar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (salvando) return;
    setSalvando(true); setErros({}); setMensagem("");
    const dados: Record<string, unknown> = {};
    for (const campo of campos[recurso]) {
      const valor = valores[campo.nome] ?? "";
      if (campo.nome === "password" && !valor && editando) continue;
      if (["obra_id", "perfil", "ano_publicacao"].includes(campo.nome)) dados[campo.nome] = valor ? Number(valor) : null;
      else dados[campo.nome] = valor || (["isbn", "editora"].includes(campo.nome) ? null : "");
    }
    try {
      await requisitar(recurso, editando ? "PATCH" : "POST", { id: editando?.id, dados });
      setEditando(undefined); setMensagem("Cadastro salvo com sucesso."); await carregar();
    } catch (erro) {
      setMensagem(erro instanceof Error ? erro.message : "Não foi possível salvar.");
      if (erro instanceof FalhaApi) setErros(erro.detalhe.erros ?? {});
    } finally { setSalvando(false); }
  }

  async function alterarEstado(registro: Registro) {
    if (salvando) return;
    setSalvando(true); setMensagem("");
    try {
      await requisitar(recurso, "PATCH", { id: registro.id, dados: { is_active: !registro.is_active } });
      setMensagem(registro.is_active ? "Cadastro desativado." : "Cadastro ativado.");
      await carregar();
    } catch (erro) {
      setMensagem(erro instanceof Error ? erro.message : "Não foi possível alterar o cadastro.");
    } finally { setSalvando(false); }
  }

  return <section className="cadastros">
    <div className="cadastros-heading"><h1>{titulos[recurso]}</h1>{!acessoNegado && <button className="primary-button" type="button" onClick={() => abrir(null)}>Novo cadastro</button>}</div>
    {mensagem && editando === undefined && <p className="cadastros-message" role="status">{mensagem}</p>}
    {detalhe && <section className="cadastros-form" aria-labelledby="titulo-detalhes">
      <h2 id="titulo-detalhes">Detalhes do cadastro</h2>
      <p><strong>ID</strong> {detalhe.id}</p>
      {campos[recurso].filter(campo => campo.nome !== "password").map(campo =>
        <p key={campo.nome}><strong>{campo.rotulo}</strong> {campo.nome === "obra_id" ? obras.find(obra => obra.id === detalhe.obra_id)?.titulo ?? String(detalhe.obra_id) : campo.nome === "perfil" ? ({1:"Aluno",2:"Bibliotecário",3:"Administrador"} as Record<number,string>)[Number(detalhe.perfil)] : String(detalhe[campo.nome] ?? "—")}</p>
      )}
      <p><strong>Status</strong> <span className={`cadastros-status ${detalhe.is_active ? "cadastros-status-ativo" : "cadastros-status-inativo"}`}>{detalhe.is_active ? "Ativo" : "Inativo"}</span></p>
      {recurso === "exemplares" && <p><strong>Situação</strong> {detalhe.situacao === 1 ? "Disponível" : "Emprestado"}</p>}
      <div className="cadastros-actions"><button type="button" onClick={() => setDetalhe(null)}>Fechar</button></div>
    </section>}
    {editando !== undefined && <dialog ref={dialogRef} className="cadastros-dialog" aria-labelledby="titulo-formulario" onCancel={event => { if (salvando) event.preventDefault(); }} onClose={() => setEditando(undefined)}>
      <form className="cadastros-form cadastros-dialog-form" onSubmit={salvar}>
      <h2 id="titulo-formulario">{editando ? "Editar cadastro" : "Novo cadastro"}</h2>
      {mensagem && <p className="cadastros-message" role="alert">{mensagem}</p>}
      {campos[recurso].map(campo => <div className="cadastros-field" key={campo.nome}>
        <label htmlFor={campo.nome}>{campo.rotulo}</label>
        {campo.nome === "perfil" ? <select id={campo.nome} value={valores[campo.nome]} onChange={e => setValores({ ...valores, [campo.nome]: e.target.value })} required>
          <option value="">Selecione</option><option value="1">Aluno</option><option value="2">Bibliotecário</option><option value="3">Administrador</option>
        </select> : campo.nome === "obra_id" ? <select id={campo.nome} value={valores[campo.nome]} onChange={e => setValores({ ...valores, [campo.nome]: e.target.value })} required>
          <option value="">Selecione</option>{obras.filter(obra => obra.is_active || obra.id === editando?.obra_id).map(obra => <option key={obra.id} value={obra.id}>{obra.titulo}{!obra.is_active ? " (inativa)" : ""}</option>)}
        </select> : <input id={campo.nome} type={campo.tipo ?? "text"} value={valores[campo.nome] ?? ""} required={campo.obrigatorio || (campo.nome === "password" && !editando)} onChange={e => setValores({ ...valores, [campo.nome]: e.target.value })} aria-describedby={erros[campo.nome] ? `erro-${campo.nome}` : undefined} />}
        {erros[campo.nome] && <p id={`erro-${campo.nome}`} className="cadastros-error" role="alert">{erros[campo.nome].join(" ")}</p>}
      </div>)}
      <div className="cadastros-actions"><button className="primary-button" disabled={salvando}>{salvando ? "Salvando..." : "Salvar"}</button><button type="button" disabled={salvando} onClick={() => setEditando(undefined)}>Cancelar</button></div>
      </form>
    </dialog>}
    {recurso === "obras" && <form className="catalog-search" onSubmit={e => { e.preventDefault(); setPagina(1); setTermo(busca); }}>
      <label htmlFor="busca">Buscar por título, autor ou ISBN</label><div><input id="busca" value={busca} onChange={e => setBusca(e.target.value)} /><button className="primary-button">Buscar</button></div>
    </form>}
    {carregando ? <p role="status">Carregando...</p> : falhaLista ? (!acessoNegado && <button type="button" onClick={() => void carregar()}>Tentar novamente</button>) : registros.length === 0 ? <p>Nenhum cadastro encontrado.</p> :
      <div className="catalog-table"><table><thead><tr>
        {recurso === "obras" ? <><th>Título</th><th>Autor</th><th>Disponíveis</th></> : recurso === "usuarios" ? <><th>Nome</th><th>E-mail</th><th>Perfil</th></> : <><th>Código</th><th>Obra</th><th>Situação</th></>}
        <th>Status</th><th>Ações</th></tr></thead><tbody>
        {registros.map(registro => <tr key={registro.id}>
          {recurso === "obras" ? <><td>{String(registro.titulo)}</td><td>{String(registro.autor)}</td><td>{String(registro.quantidade_disponivel)}</td></> :
            recurso === "usuarios" ? <><td>{String(registro.nome)}</td><td>{String(registro.email)}</td><td>{({1:"Aluno",2:"Bibliotecário",3:"Administrador"} as Record<number,string>)[Number(registro.perfil)]}</td></> :
            <><td>{String(registro.codigo)}</td><td>{obras.find(obra => obra.id === registro.obra_id)?.titulo ?? `Obra #${registro.obra_id}`}</td><td>{registro.situacao === 1 ? "Disponível" : "Emprestado"}</td></>}
          <td><span className={`cadastros-status ${registro.is_active ? "cadastros-status-ativo" : "cadastros-status-inativo"}`}>{registro.is_active ? "Ativo" : "Inativo"}</span></td><td><div className="cadastros-actions"><button type="button" onClick={() => setDetalhe(registro)}>Detalhes</button><button type="button" onClick={() => abrir(registro)}>Editar</button><button type="button" disabled={salvando} onClick={() => void alterarEstado(registro)}>{registro.is_active ? "Desativar" : "Ativar"}</button></div></td>
        </tr>)}</tbody></table></div>}
    {paginacao && <nav aria-label="Paginação" className="catalog-pagination"><button disabled={!paginacao.previous} onClick={() => setPagina(pagina - 1)}>Anterior</button><span>Página {pagina}</span><button disabled={!paginacao.next} onClick={() => setPagina(pagina + 1)}>Próxima</button></nav>}
  </section>;
}
