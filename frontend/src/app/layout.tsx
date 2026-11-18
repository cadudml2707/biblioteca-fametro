import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "Biblioteca FAMETRO | Gestão", description: "Área de gestão da Biblioteca FAMETRO" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
