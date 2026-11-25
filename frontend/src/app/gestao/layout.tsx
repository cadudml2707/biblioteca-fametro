"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { ArrowRight, BookCopy, BookOpen, CalendarClock, ChartNoAxesCombined, CircleHelp, LayoutDashboard, LibraryBig, LogOut, Settings2, Users } from "lucide-react";
import { Brand } from "@/components/brand";
import { sharedSession, type User } from "@/lib/auth";

const sections = [
  { label: "Início", icon: LayoutDashboard, active: true },
  { label: "Obras", icon: BookOpen, href: "/gestao/obras" },
  { label: "Exemplares", icon: LibraryBig, href: "/gestao/exemplares" },
  { label: "Reservas", icon: CalendarClock, href: "/gestao/reservas" },
  { label: "Circulação", icon: BookCopy, href: "/gestao/circulacao" },
  { label: "Relatórios", icon: ChartNoAxesCombined },
];
const adminSections = [{ label: "Usuários", icon: Users, href: "/gestao/usuarios" }, { label: "Configurações", icon: Settings2, href: "/gestao/configuracoes" }];

export default function GestaoLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [loggingOut, setLoggingOut] = useState(false);
  const load = useCallback(async () => {
    setState("loading");
    try { const current = await sharedSession(); if (!current) { router.replace("/login"); return; } setUser(current); setState("ready"); }
    catch { setState("error"); }
  }, [router]);
  useEffect(() => { void load(); }, [load]);
  async function logout() {
    setLoggingOut(true);
    try { const response = await fetch("/api/auth/logout", { method: "POST" }); const data = await response.json(); if (!data.revogado) sessionStorage.setItem("logout-aviso", "A sessão local foi encerrada, mas não foi possível confirmar a revogação no servidor."); }
    catch { sessionStorage.setItem("logout-aviso", "Não foi possível confirmar a saída. Tente novamente."); setLoggingOut(false); return; }
    router.replace("/login");
  }
  if (state === "loading") return <main className="state-page"><div className="spinner"/><p>Carregando sessão...</p></main>;
  if (state === "error") return <main className="state-page"><div className="state-card"><CircleHelp size={30}/><h1>Não foi possível conectar</h1><p>O servidor está indisponível no momento. Tente novamente em instantes.</p><button className="primary-button" onClick={load}>Tentar novamente <ArrowRight size={18}/></button></div></main>;
  if (!user) return null;
  const profile = user.perfil === 3 ? "Administrador" : "Bibliotecário";
  const firstName = user.nome.trim().split(/\s+/)[0];
  return (
    <div className="app-shell">
      <a className="skip-link" href="#conteudo">Pular para o conteúdo</a>
      <aside className="sidebar">
        <div className="sidebar-top"><Brand /></div>
        <nav aria-label="Navegação principal">
          {sections.map(({ label, icon: Icon, active, href }) =>
            active || href ? (
              <a href={href ?? "/gestao"} key={label} className={pathname === (href ?? "/gestao") ? "nav-item active" : "nav-item"} aria-current={pathname === (href ?? "/gestao") ? "page" : undefined}>
                <Icon size={19} aria-hidden="true" /> {label}
              </a>
            ) : (
              <div className="nav-item unavailable" key={label} aria-disabled="true">
                <Icon size={19} aria-hidden="true" /> {label}
              </div>
            ),
          )}
          {user.perfil === 3 && (
            <>
              <div className="nav-section admin-section">Administração</div>
              {adminSections.map(({ label, icon: Icon, href }) => (
                <a href={href} key={label} className={pathname === href ? "nav-item active" : "nav-item"} aria-current={pathname === href ? "page" : undefined}>
                  <Icon size={19} aria-hidden="true" /> {label}
                </a>
              ))}
            </>
          )}
        </nav>
        <div className="sidebar-bottom">
          <button className="logout" onClick={logout} disabled={loggingOut}>
            <LogOut size={18} aria-hidden="true" />
            {loggingOut ? "Saindo..." : "Sair da conta"}
          </button>
        </div>
      </aside>
      <div className="app-main">
        <header className="app-header">
          <strong>Biblioteca</strong>
          <div className="header-account">
            <div className="header-user"><strong>{user.nome}</strong><span>{profile}</span></div>
            <div className="avatar" aria-hidden="true">{firstName.slice(0, 1).toUpperCase()}</div>
          </div>
        </header>
        <main id="conteudo" className="dashboard">{children}</main>
      </div>
    </div>
  );
}
