import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/aluno",
    name: "Biblioteca FAMETRO",
    short_name: "Biblioteca",
    description: "Consulte o acervo e acompanhe suas reservas.",
    start_url: "/aluno",
    scope: "/",
    display: "standalone",
    background_color: "#f5f8fc",
    theme_color: "#07386c",
    icons: [
      { src: "/icone-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icone-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
