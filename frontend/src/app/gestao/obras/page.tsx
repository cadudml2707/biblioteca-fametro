"use client";

import { useEffect, useState } from "react";
import { CabecalhoPagina, EstadoCarregando, EstadoErro, EstadoVazio, Paginacao } from "@/components/gestao/estados";
import { consultarObras, type Obra, type Pagina } from "@/lib/api/obras";

export default function ObrasPage() {
  const [busca, setBusca] = useState("");
  const [termo, setTermo] = useState("");
  const [pagina, setPagina] = useState(1);
  const [dados, setDados] = useState<Pagina<Obra> | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    let ativa = true;
    setDados(null);
    setErro("");
    consultarObras(termo, pagina).then(resultado => { if (ativa) setDados(resultado); })
      .catch(falha => { if (ativa) setErro(falha.message); });
    return () => { ativa = false; };
  }, [termo, pagina, tentativa]);

  return <section className="catalog-page">
    <CabecalhoPagina titulo="Obras" />
    <form className="catalog-search" onSubmit={event => { event.preventDefault(); setPagina(1); setTermo(busca); }}>
      <label htmlFor="busca-obras">Buscar por título, autor ou ISBN</label>
      <div><input id="busca-obras" value={busca} onChange={event => setBusca(event.target.value)} /><button className="primary-button">Buscar</button></div>
    </form>
    {erro ? <EstadoErro mensagem={erro} tentarNovamente={() => setTentativa(valor => valor + 1)} />
      : !dados ? <EstadoCarregando mensagem="Carregando obras..." />
      : dados.results.length === 0 ? <EstadoVazio mensagem="Nenhuma obra encontrada." />
      : <><div className="catalog-table"><table><thead><tr><th>Título</th><th>Autor</th><th>ISBN</th><th>Disponíveis</th></tr></thead>
        <tbody>{dados.results.map(obra => <tr key={obra.id}><td>{obra.titulo}</td><td>{obra.autor}</td><td>{obra.isbn || "—"}</td><td>{obra.quantidade_disponivel}</td></tr>)}</tbody></table></div>
        <Paginacao pagina={pagina} anterior={!!dados.previous} proxima={!!dados.next} alterar={setPagina} /></>}
  </section>;
}
