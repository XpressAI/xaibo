<div class="hero-section" style="margin-top: -4em">
      <h1 style="color: white">
      <svg xmlns="http://www.w3.org/2000/svg" style="margin-bottom: -8px" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot-icon lucide-bot"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
       Xaibo
      </h1>
      <h2 style="margin-top: -1rem">The Modular AI Agent Framework</h2>
      <p>Build robust, production-ready AI agents that are easy to test and maintain. Stop fighting complexity, start shipping with clean, protocol-based design.</p>
      <div style="margin-top: 2rem;">
        <a href="https://github.com/xpressai/xaibo" class="md-button md-button--primary" style="margin-right: 1rem;">
          View on GitHub
        </a>
        <a href="tutorial/" class="md-button " style="background: rgba(255,255,255,0.2); color: white;">
          Get Started
        </a>
      </div>
    </div>

## What is Xaibo?

Xaibo is a powerful, protocol-driven framework that enables developers to build sophisticated AI agents with unprecedented flexibility and modularity. By using well-defined interfaces and dependency injection, Xaibo allows you to create, test, and deploy AI systems that are both robust and easily maintainable.

!!! tip "Quick Start"
    **Prerequisites:** Python 3.10 or higher installed
    
    Get up and running with Xaibo in 60 seconds:
    ```bash
    pip install uv
    uvx xaibo init my_project
    cd my_project
    uv run xaibo dev
    ```
    This will give you an agent that you can start modifiying immediately.

    Follow our [Tutorial](tutorial/index.md) to learn how everything works.

## Why Choose Xaibo?

<div class="feature-grid">
  <div class="feature-card">
    <h3>🧩 Swap Models & Tools Instantly</h3>
    <p>A modular architecture saves time and reduces complexity. Want to switch from OpenAI to Anthropic? Just change a single line in your configuration.</p>
  </div>
  <div class="feature-card">
    <h3>🔌 Test with Confidence</h3>
    <p>Components communicate through well-defined protocols. This creates clean boundaries, enabling superior unit and integration testing with predictable mocks.</p>
  </div>
  <div class="feature-card">
    <h3>🔍 Visualize Every Step</h3>
    <p>Transparent proxies capture every component interaction, providing detailed runtime insights and a powerful visual debugger so you always know what your agent is doing.</p>
  </div>
</div>

## See Xaibo in Action: The Visual Debug Interface

Xaibo includes a powerful debug UI that visualizes your agent's operations in real-time:

<div style="display: flex; gap: 10px; margin: 20px 0;">
  <div style="flex: 1;">
    <img src="images/sequence-diagram.png" alt="Xaibo Debug UI - Sequence Diagram Overview" width="100%">
    <p><em>Sequence Diagram Overview</em></p>
  </div>
  <div style="flex: 1;">
    <img src="images/detail-view.png" alt="Xaibo Debug UI - Detail View" width="100%">
    <p><em>Detail View of Component Interactions</em></p>
  </div>
</div>

## A Framework Designed for Developers

<div class="grid cards" markdown>

-   :material-puzzle-outline: **Protocol-Based Architecture**

    ---

    Components interact through well-defined interfaces, enabling easy testing with mocks and ensuring clean boundaries within your system.

-   :material-swap-horizontal: **Dependency Injection**

    ---

    Explicitly declare component dependencies. This makes it trivial to swap implementations - for testing or for production - without refactoring your code.

-   :material-eye-outline: **Transparent Proxies**

    ---

    Every component is automatically wrapped with observability proxies that capture parameters, timing, and exceptions for complete visibility.

-   :material-chart-timeline-variant: **Comprehensive Event System**

    ---

    A built-in event system provides real-time monitoring, call sequence tracking, and performance insights out of the box. 

-   :material-wrench: **Arbitrary Tool Support**

    ---

    Use tools implemented in simple python, use MCP servers or integrate whatever other APIs you want as tools.

-   :material-api: **Production-Ready API Server**

    ---

    Includes a built-in web server with an OpenAI-compatible API and MCP (Model Context Protocol) support for seamless integration into existing ecosystems.

</div>

---

## Your Gateway to the Xaibo Ecosystem

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Getting Started Tutorial](tutorial/index.md)**

    ---

    Your first step. Build a complete AI agent with tools and understand Xaibo's core architecture.

-   :material-book-open-page-variant: **[How-to Guides](how-to/index.md)**

    ---

    Practical recipes for installation, tool integration, LLM configuration, and deployment.

-   :material-brain: **[Core Concepts](explanation/index.md)**

    ---

    A deep dive into protocols, modules, dependency injection, and Xaibo's design principles.

-   :material-api: **[API Reference](reference/index.md)**

    ---

    Complete technical documentation for every module, protocol, and CLI command.

-   :material-tools: **[Building Tools](tutorial/building-tools.md)**

    ---

    Learn to create custom Python and MCP tools that extend your agent's capabilities

-   :material-cog: **[Architecture Guide](explanation/architecture/protocols.md)**

    ---

    Understand Xaibo's protocol-based architecture and transparent proxy system

</div>


---

## Join the Community

<div class="grid cards" markdown>

-   :fontawesome-brands-github: **[GitHub Repository](https://github.com/xpressai/xaibo)**

    ---

    Contribute to the source code, file issues, and track development progress.

-   :fontawesome-brands-discord: **[Discord Community](https://discord.gg/uASMzSSVKe)**

    ---

    Join our community for support, to ask questions, and to share what you're building.

-   :material-email: **[Contact Us](mailto:hello@xpress.ai)**

    ---

    Get in touch for direct inquiries and support.

</div>

---

# Ready to Build Better Agents?
[Start the Tutorial](tutorial/index.md) to create your first Xaibo agent, or dive into [Core Concepts](explanation/index.md) to understand the framework's architecture.
