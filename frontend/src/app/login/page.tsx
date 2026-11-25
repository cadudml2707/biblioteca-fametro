"use client";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { Brand } from "@/components/brand";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { const aviso = sessionStorage.getItem("logout-aviso"); if (aviso) { setError(aviso); sessionStorage.removeItem("logout-aviso"); } }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    setLoading(true); setError("");
    try {
      const response = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
      const data = await response.json();
      if (!response.ok) { setError(data.mensagem || "Não foi possível entrar. Verifique seus dados."); return; }
      router.replace(data.usuario.perfil === 1 ? "/aluno" : "/gestao");
    } catch { setError("Não foi possível conectar ao servidor. Tente novamente."); }
    finally { setLoading(false); }
  }

  return (
    <main className="login-layout">
      <section className="login-story" aria-label="Biblioteca FAMETRO">
        <div className="login-story-copy">
          <span className="login-story-kicker">BIBLIOTECA FAMETRO</span>
          <h2>Conhecimento que transforma.</h2>
          <p>Uma gestão mais simples para aproximar pessoas e conhecimento.</p>
        </div>
        <div className="book-art">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-book book-one" />
          <div className="art-book book-two" />
          <div className="art-book book-three" />
        </div>
      </section>
      <section className="login-main" aria-labelledby="login-title">
        <div className="login-box">
          <Brand />
          <h1 id="login-title">Acesse a biblioteca</h1>
          <form onSubmit={handleSubmit} className="login-form">
            <div className="input-wrap">
              <Mail size={18} aria-hidden="true" />
              <input id="email" aria-label="E-mail" type="email" placeholder="seu.email@fametro.edu.br" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>
            <div className="input-wrap">
              <LockKeyhole size={18} aria-hidden="true" />
              <input id="password" aria-label="Senha" type={visible ? "text" : "password"} placeholder="Digite sua senha" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required />
              <button type="button" className="visibility" onClick={() => setVisible(!visible)} aria-label={visible ? "Ocultar senha" : "Mostrar senha"}>
                {visible ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="primary-button" disabled={loading} type="submit">
              <span>{loading ? "Entrando..." : "Entrar"}</span>
              <ArrowRight size={19} aria-hidden="true" />
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
