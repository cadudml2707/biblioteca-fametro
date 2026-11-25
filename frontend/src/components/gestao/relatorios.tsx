"use client";

import { useEffect, useState } from "react";
import { BookOpen, BookCopy, LibraryBig, AlertCircle, ArrowDownToLine, ArrowUpFromLine, BookCheck, BookMarked } from "lucide-react";
import { FalhaApi } from "@/lib/api/cliente";
import { consultarRelatorio, type PeriodoRelatorio, type RelatorioResumo } from "@/lib/api/relatorios";

function dataEmManaus(data: Date) {
  const partes = new Intl.DateTimeFormat("en", {
    timeZone: "America/Manaus",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(data);
  const valor = (tipo: string) => partes.find(parte => parte.type === tipo)?.value ?? "";
  return `${valor("year")}-${valor("month")}-${valor("day")}`;
}

function periodoInicial(): PeriodoRelatorio {
  const hoje = dataEmManaus(new Date());
  return { data_inicio: `${hoje.slice(0, 7)}-01`, data_fim: hoje };
}

const numero = new Intl.NumberFormat("pt-BR");

export function Relatorios() {
  const [periodo, setPeriodo] = useState<PeriodoRelatorio>(periodoInicial);
  const [aplicado, setAplicado] = useState<PeriodoRelatorio>(periodoInicial);
  const [relatorio, setRelatorio] = useState<RelatorioResumo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [semAcesso, setSemAcesso] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setCarregando(true);
    setErro("");
    setSemAcesso(false);
    consultarRelatorio(aplicado, controller.signal)
      .then(dados => setRelatorio(dados))
      .catch(falha => {
        if (falha instanceof DOMException && falha.name === "AbortError") return;
        setSemAcesso(falha instanceof FalhaApi && falha.status === 403);
        setErro(falha instanceof Error ? falha.message : "Não foi possível carregar os relatórios.");
      })
      .finally(() => { if (!controller.signal.aborted) setCarregando(false); });
    return () => controller.abort();
  }, [aplicado]);

  function aplicar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAplicado({ ...periodo });
  }

  const metricas = relatorio ? [
    { rotulo: "Obras ativas", total: relatorio.acervo.obras_ativas, icon: BookOpen, descricao: "Títulos ativos no acervo" },
    { rotulo: "Exemplares ativos", total: relatorio.acervo.exemplares_ativos, icon: LibraryBig, descricao: "Exemplares no acervo", cor: "turquesa" },
    { rotulo: "Exemplares disponíveis", total: relatorio.acervo.exemplares_disponiveis, icon: BookCheck, descricao: "Disponíveis para retirada", cor: "sucesso" },
    { rotulo: "Exemplares emprestados", total: relatorio.acervo.exemplares_emprestados, icon: BookCopy, descricao: "Situação atual do acervo" },
    { rotulo: "Empréstimos ativos", total: relatorio.emprestimos.ativos, icon: BookMarked, descricao: "Empréstimos em aberto", cor: "turquesa" },
    { rotulo: "Empréstimos em atraso", total: relatorio.emprestimos.atrasados, icon: AlertCircle, descricao: "Exigem acompanhamento", alerta: relatorio.emprestimos.atrasados > 0 },
  ] : [];

  return <section className="cadastros relatorios painel-relatorios">
    <div className="cadastros-heading"><div><h1>Visão geral</h1></div></div>
    <form className="relatorios-filtros" onSubmit={aplicar}>
      <div className="painel-filtro-titulo"><strong>Indicadores</strong><span>Selecione o período</span></div>
      <label htmlFor="relatorio-data-inicio">De<input id="relatorio-data-inicio" type="date" required value={periodo.data_inicio} max={periodo.data_fim} onChange={event => setPeriodo(atual => ({ ...atual, data_inicio: event.target.value }))} /></label>
      <label htmlFor="relatorio-data-fim">Até<input id="relatorio-data-fim" type="date" required value={periodo.data_fim} min={periodo.data_inicio} max={dataEmManaus(new Date())} onChange={event => setPeriodo(atual => ({ ...atual, data_fim: event.target.value }))} /></label>
      <button className="primary-button" disabled={carregando}>{carregando ? "Carregando..." : "Aplicar período"}</button>
    </form>
    {semAcesso ? <p role="alert" className="relatorios-aviso">Seu perfil não tem acesso aos relatórios.</p> : erro ? <div className="relatorios-erro" role="alert"><p>{erro}</p><button type="button" onClick={() => setAplicado({ ...aplicado })}>Tentar novamente</button></div> : carregando ? <p role="status">Carregando relatórios...</p> : relatorio && <>
      <div className="relatorios-metricas">
        {metricas.map(metrica => <article className={`relatorio-metrica${metrica.cor ? ` painel-cor-${metrica.cor}` : ""}${metrica.alerta ? " relatorio-metrica-alerta" : ""}`} key={metrica.rotulo}>
          <div className="painel-metrica-topo"><h2>{metrica.rotulo}</h2><span className="painel-metrica-icone"><metrica.icon size={20} aria-hidden="true" /></span></div><p>{numero.format(metrica.total)}</p><span className="painel-metrica-descricao">{metrica.descricao}</span>
        </article>)}
      </div>
      <div className="painel-graficos">
        <section className="painel-grafico"><h2>Reservas por situação</h2>
          {relatorio.reservas.total_periodo === 0 ? <div className="painel-vazio">Nenhuma reserva encontrada nesse período.</div> : <div className="painel-barras">{relatorio.reservas.por_situacao.map(item => <div className={`painel-barra-linha painel-situacao-${item.situacao}`} key={item.situacao}><div><span>{item.descricao}</span><strong>{numero.format(item.total)}</strong></div><div className="painel-barra-fundo"><span style={{ width: `${item.total / relatorio.reservas.total_periodo * 100}%` }} /></div></div>)}</div>}
        </section>
        <section className="painel-grafico"><h2>Movimentações no período</h2>
          <div className="painel-movimentos"><div><span className="painel-movimento-icone"><ArrowUpFromLine size={22}/></span><div><strong>{numero.format(relatorio.emprestimos.retiradas_periodo)}</strong><span>Retiradas</span></div></div><div><span className="painel-movimento-icone"><ArrowDownToLine size={22}/></span><div><strong>{numero.format(relatorio.emprestimos.devolucoes_periodo)}</strong><span>Devoluções</span></div></div></div>
        </section>
      </div>
    </>}
  </section>;
}
