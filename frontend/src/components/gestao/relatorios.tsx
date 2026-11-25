"use client";

import { useEffect, useState } from "react";
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
const dataPt = (valor: string) => valor.split("-").reverse().join("/");

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
    { rotulo: "Obras ativas", total: relatorio.acervo.obras_ativas },
    { rotulo: "Exemplares ativos", total: relatorio.acervo.exemplares_ativos },
    { rotulo: "Exemplares disponíveis", total: relatorio.acervo.exemplares_disponiveis },
    { rotulo: "Exemplares emprestados", total: relatorio.acervo.exemplares_emprestados },
    { rotulo: "Empréstimos ativos", total: relatorio.emprestimos.ativos },
    { rotulo: "Empréstimos em atraso", total: relatorio.emprestimos.atrasados, alerta: relatorio.emprestimos.atrasados > 0 },
    { rotulo: "Retiradas no período", total: relatorio.emprestimos.retiradas_periodo },
    { rotulo: "Devoluções no período", total: relatorio.emprestimos.devolucoes_periodo },
    { rotulo: "Reservas solicitadas no período", total: relatorio.reservas.total_periodo },
  ] : [];

  return <section className="cadastros relatorios">
    <div className="cadastros-heading"><div><h1>Relatórios</h1><p className="relatorios-intro">Resumo do acervo e da circulação. As datas seguem o fuso de Manaus.</p></div></div>
    <form className="relatorios-filtros" onSubmit={aplicar}>
      <label htmlFor="relatorio-data-inicio">De<input id="relatorio-data-inicio" type="date" required value={periodo.data_inicio} max={periodo.data_fim} onChange={event => setPeriodo(atual => ({ ...atual, data_inicio: event.target.value }))} /></label>
      <label htmlFor="relatorio-data-fim">Até<input id="relatorio-data-fim" type="date" required value={periodo.data_fim} min={periodo.data_inicio} max={dataEmManaus(new Date())} onChange={event => setPeriodo(atual => ({ ...atual, data_fim: event.target.value }))} /></label>
      <button className="primary-button" disabled={carregando}>{carregando ? "Carregando..." : "Aplicar período"}</button>
    </form>
    {semAcesso ? <p role="alert" className="relatorios-aviso">Seu perfil não tem acesso aos relatórios.</p> : erro ? <div className="relatorios-erro" role="alert"><p>{erro}</p><button type="button" onClick={() => setAplicado({ ...aplicado })}>Tentar novamente</button></div> : carregando ? <p role="status">Carregando relatórios...</p> : relatorio && <>
      <p className="relatorios-periodo" aria-live="polite">Período aplicado: {dataPt(relatorio.periodo.data_inicio)} a {dataPt(relatorio.periodo.data_fim)}</p>
      <div className="relatorios-metricas">
        {metricas.map(metrica => <article className={`relatorio-metrica${metrica.alerta ? " relatorio-metrica-alerta" : ""}`} key={metrica.rotulo}>
          <h2>{metrica.rotulo}</h2><p>{numero.format(metrica.total)}</p>
        </article>)}
      </div>
      <div className="relatorios-tabela">
        <h2>Reservas solicitadas no período por situação atual</h2>
        {relatorio.reservas.total_periodo === 0 && <p>Nenhuma reserva encontrada nesse período.</p>}
        {relatorio.reservas.por_situacao.length === 0 ? null : <div className="catalog-table"><table><thead><tr><th>Situação</th><th>Total</th></tr></thead><tbody>
          {relatorio.reservas.por_situacao.map(item => <tr key={item.situacao}><td>{item.descricao}</td><td>{numero.format(item.total)}</td></tr>)}
        </tbody></table></div>}
      </div>
    </>}
  </section>;
}
