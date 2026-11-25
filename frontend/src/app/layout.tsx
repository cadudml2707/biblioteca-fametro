import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Biblioteca FAMETRO",
  description: "Consulte o acervo e acompanhe suas reservas na Biblioteca FAMETRO.",
  appleWebApp: { capable: true, title: "Biblioteca", statusBarStyle: "default" },
  icons: { apple: "/icone-180.png" },
};
export const viewport: Viewport = { themeColor: "#07386c" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
