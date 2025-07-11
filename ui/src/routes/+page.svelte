<script>
  const docsLinks = [
    { emoji: "🚀", title: "Getting Started Tutorial", href: "https://xaibo.ai/tutorial/" },
    { emoji: "📖", title: "How-to Guides",           href: "https://xaibo.ai/how-to/" },
    { emoji: "🧠", title: "Core Concepts",           href: "https://xaibo.ai/explanation/" },
    { emoji: "📚", title: "API Reference",           href: "https://xaibo.ai/reference/" },
    { emoji: "🛠️", title: "Building Tools",          href: "https://xaibo.ai/tutorial/building-tools/" },
    { emoji: "⚙️", title: "Architecture Guide",      href: "https://xaibo.ai/explanation/architecture/protocols/" },
  ];

  const communityLinks = [
    { emoji: "💻", title: "GitHub Repository", href: "https://github.com/xpressai/xaibo" },
    { emoji: "💬", title: "Discord Community", href: "https://discord.gg/uASMzSSVKe" },
    { emoji: "✉️", title: "Contact Us",        href: "mailto:hello@xpress.ai" },
  ];
</script>

<style>
  main {
    max-width: 640px;
    margin: 2rem auto;
    padding: 0 1rem;
    font-family: sans-serif;
  }

  .hero-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    grid-template-rows: auto auto;
    column-gap: 1rem;
    align-items: center;
    margin-bottom: 1rem;
  }
  .hero-grid svg {
    grid-row: 1 / span 2;
    width: 64px;
    height: 64px;
  }
  .hero-title {
    grid-column: 2;
    grid-row: 1;
    font-size: 2rem;
    margin: 0;
  }
  .hero-subtitle {
    grid-column: 2;
    grid-row: 2;
    font-size: 1.25rem;
    color: #555;
    margin: 0;
  }

  .tagline {
    font-size: 1rem;
    margin-bottom: 2rem;
    line-height: 1.5;
  }

  section h2 {
    font-size: 1.5rem;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.25rem;
  }

  .docs-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  .card {
    background: #f9f9f9;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  .card a {
    color: #1e40af;
    text-decoration: none;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .card a:hover {
    text-decoration: underline;
  }

  .community-section h2 {
    margin-top: 2rem;
  }

  .community {
    text-align: center;
    font-size: 1rem;
  }
  .community a {
    color: #1e40af;
    text-decoration: none;
    margin: 0 0.25rem;
  }
  .community a:hover {
    text-decoration: underline;
  }
  .community span.sep {
    color: #888;
  }
</style>

<main>
  <div class="hero-grid">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/>
      <path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>
    </svg>
    <h1 class="hero-title">Xaibo</h1>
    <div class="hero-subtitle">The Modular AI Agent Framework</div>
  </div>

  <div class="tagline">
    Ready to build robust, production-ready AI agents that are easy to test
    and maintain and ship with clean, protocol-based design?
  </div>

  <section>
    <h2>Documentation</h2>
    <div class="docs-grid">
      {#each docsLinks as { emoji, title, href }}
        <div class="card">
          <a href={href} target="_blank" rel="noopener">
            <span>{emoji}</span>
            <span>{title}</span>
          </a>
        </div>
      {/each}
    </div>
  </section>

  <section class="community-section">
    <h2>Community</h2>
    <div class="community">
      {#each communityLinks as { emoji, title, href }, i}
        <a href={href} target="_blank" rel="noopener">{emoji} {title}</a>
        {#if i < communityLinks.length - 1}
          <span class="sep">|</span>
        {/if}
      {/each}
    </div>
  </section>
</main>
