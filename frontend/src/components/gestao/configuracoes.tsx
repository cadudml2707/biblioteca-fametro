"use client";

import { useCallback, useEffect, useState } from "react";
import { FalhaApi } from "@/lib/api/cliente";
import { requisitarConfiguracao, type Configuracao, type Parametros } from "@/lib/api/configuracoes";

const CAMPOS: { nome: keyof Parametros; rotulo: string; descricao: string }[] = [
  { nome: "limite_reservas_ativas", rotulo: "Reservas ativas por aluno", descricao: "Máximo de reservas solicitadas ou confirmadas ao mesmo tempo." },
  { nome: "limite_emprestimos_ativos", rotulo: "Empréstimos ativos por aluno", descricao: "Máximo de exemplares emprestados ao mesmo tempo." },
  { nome: "prazo_emprestimo_dias", rotulo: "Prazo de empréstimo (dias)", descricao: "Prazo contado em dias corridos a partir da retirada." },
  { nome: "prazo_retirada_reserva_dias", rotulo: "Prazo para retirar reserva (dias)", descricao: "Prazo em dias corridos para retirar após a confirmação." },
];

type Valores = Record<keyof Parametros, string>;
const vazio: Valores = {
  limite_reservas_ativas: "",
  limite_emprestimos_ativos: "",
  prazo_emprestimo_dias: "",
  prazo_retirada_reserva_dias: "",
};

function paraFormulario(configuracao: Configuracao): Valores {
  return {
    limite_reservas_ativas: String(configuracao.limite_reservas_ativas),
    limite_emprestimos_ativos: String(configuracao.limite_emprestimos_ativos),
    prazo_emprestimo_dias: String(configuracao.prazo_emprestimo_dias),
    prazo_retirada_reserva_dias: String(configuracao.prazo_retirada_reserva_dias),
  };
}

export function Configuracoes() {
  const [configuracao, setConfiguracao] = useState<Configuracao | null>(null);
  const [valores, setValores] = useState<Valores>(vazio);
  const [erros, setErros] = useState<Record<string, string[]>>({});
  const [mensagem, setMensagem] = useState("");
  const [sucesso, setSucesso] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [falha, setFalha] = useState(false);
  const [semAcesso, setSemAcesso] = useState(false);
  const [salvando, setSalvando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setFalha(false);
    setSemAcesso(false);
    setMensagem("");
    try {
      const atual = await requisitarConfiguracao<Configuracao>("GET");
      setConfiguracao(atual);
      setValores(paraFormulario(atual));
    } catch (erro) {
      if (erro instanceof FalhaApi && erro.status === 404) {
        setConfiguracao(null);
        setValores(vazio);
      } else {
        setFalha(true);
        setSemAcesso(erro instanceof FalhaApi && erro.status === 403);
        setMensagem(erro instanceof Error ? erro.message : "Não foi possível carregar a configuração.");
      }
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => { void carregar(); }, [carregar]);

  async function salvar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (salvando) return;
    setSalvando(true);
    setErros({});
    setMensagem("");
    setSucesso(false);

    const dados: Parametros = {
      limite_reservas_ativas: Number(valores.limite_reservas_ativas),
      limite_emprestimos_ativos: Number(valores.limite_emprestimos_ativos),
      prazo_emprestimo_dias: Number(valores.prazo_emprestimo_dias),
      prazo_retirada_reserva_dias: Number(valores.prazo_retirada_reserva_dias),
    };

    try {
      const atualizada = await requisitarConfiguracao<Configuracao>(configuracao ? "PATCH" : "POST", dados);
      setConfiguracao(atualizada);
      setValores(paraFormulario(atualizada));
      setMensagem(configuracao ? "Configuração atualizada." : "Configuração criada e ativada.");
      setSucesso(true);
    } catch (erro) {
      setMensagem(erro instanceof Error ? erro.message : "Não foi possível salvar a configuração.");
      if (erro instanceof FalhaApi) setErros(erro.detalhe.erros ?? {});
    } finally {
      setSalvando(false);
    }
  }

  if (carregando) return <section className="cadastros"><h1>Configurações</h1><p role="status">Carregando configuração...</p></section>;
  if (semAcesso) return <section className="cadastros"><h1>Configurações</h1><p role="alert">Somente administradores podem consultar e editar os parâmetros da biblioteca.</p></section>;
  if (falha) return <section className="cadastros"><h1>Configurações</h1><p role="alert" className="cadastros-message">{mensagem}</p><button type="button" onClick={() => void carregar()}>Tentar novamente</button></section>;

  return <section className="cadastros">
    <div className="cadastros-heading"><div><h1>Configurações da biblioteca</h1><p className="configuracoes-intro">Defina os limites e prazos usados nas reservas e nos empréstimos.</p></div></div>
    {mensagem && <p role={sucesso ? "status" : "alert"} className={sucesso ? "cadastros-message configuracoes-sucesso" : "cadastros-message configuracoes-erro"}>{mensagem}</p>}
    {!configuracao && <p className="configuracoes-aviso">Ainda não existe uma configuração ativa. Crie uma para habilitar solicitações de reserva, confirmações e retiradas.</p>}
    <form className="cadastros-form configuracoes-form" onSubmit={salvar}>
      {CAMPOS.map(campo => <div className="cadastros-field" key={campo.nome}>
        <label htmlFor={campo.nome}>{campo.rotulo}</label>
        <p className="configuracoes-descricao" id={`${campo.nome}-descricao`}>{campo.descricao}</p>
        <input
          id={campo.nome}
          type="number"
          min={1}
          step={1}
          required
          value={valores[campo.nome]}
          onChange={event => setValores(anterior => ({ ...anterior, [campo.nome]: event.target.value }))}
          aria-invalid={Boolean(erros[campo.nome])}
          aria-describedby={`${campo.nome}-descricao${erros[campo.nome] ? ` erro-${campo.nome}` : ""}`}
        />
        {erros[campo.nome] && <p id={`erro-${campo.nome}`} className="cadastros-error" role="alert">{erros[campo.nome].join(" ")}</p>}
      </div>)}
      <div className="cadastros-actions">
        <button className="primary-button" disabled={salvando}>{salvando ? "Salvando..." : configuracao ? "Salvar alterações" : "Ativar configuração"}</button>
        {configuracao && <button type="button" disabled={salvando} onClick={() => { setValores(paraFormulario(configuracao)); setErros({}); setMensagem(""); setSucesso(false); }}>Descartar alterações</button>}
      </div>
    </form>
  </section>;
}
