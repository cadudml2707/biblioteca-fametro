export default function GestaoPage() {
  return (
    <section className="hero-card">
      <div className="hero-copy">
        <h1>Biblioteca</h1>
        <p>Consulte o catálogo de obras.</p>
      </div>
      <div className="hero-art" aria-hidden="true">
        <div className="hero-arch" />
        <div className="hero-book hb-one" />
        <div className="hero-book hb-two" />
        <div className="hero-book hb-three" />
      </div>
    </section>
  );
}
