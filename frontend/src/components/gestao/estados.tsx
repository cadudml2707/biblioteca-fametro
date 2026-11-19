export function CabecalhoPagina({ titulo }: { titulo: string }) {
  return <h1>{titulo}</h1>;
}

export function EstadoCarregando({ mensagem }: { mensagem: string }) {
  return <p role="status">{mensagem}</p>;
}

export function EstadoVazio({ mensagem }: { mensagem: string }) {
  return <p>{mensagem}</p>;
}

export function EstadoErro({ mensagem, tentarNovamente }: { mensagem: string; tentarNovamente: () => void }) {
  return <div role="alert"><p>{mensagem}</p><button type="button" onClick={tentarNovamente}>Tentar novamente</button></div>;
}

export function ErroCampo({ mensagem, id }: { mensagem?: string; id: string }) {
  return mensagem ? <p id={id} role="alert">{mensagem}</p> : null;
}

export function Paginacao({ pagina, anterior, proxima, alterar }: {
  pagina: number; anterior: boolean; proxima: boolean; alterar: (pagina: number) => void;
}) {
  return <nav aria-label="Paginação de obras" className="catalog-pagination">
    <button type="button" disabled={!anterior} onClick={() => alterar(pagina - 1)}>Anterior</button>
    <span>Página {pagina}</span>
    <button type="button" disabled={!proxima} onClick={() => alterar(pagina + 1)}>Próxima</button>
  </nav>;
}
