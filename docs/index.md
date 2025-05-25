<div class="hero-section" style="margin-top: -4em">
      <h1 style="color: white">
      <svg xmlns="http://www.w3.org/2000/svg" style="margin-bottom: -8px" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bot-icon lucide-bot"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
       Xaibo
      </h1>
      <p>A modular agent framework designed for building flexible AI systems with clean protocol-based interfaces</p>
      <div style="margin-top: 2rem;">
        <a href="https://github.com/xpressai/xaibo" class="md-button md-button--primary" style="margin-right: 1rem;">
          View on GitHub
        </a>
        <a href="tutorial/" class="md-button " style="background: rgba(255,255,255,0.2); color: white;">
          Get Started
        </a>
      </div>
    </div>

<div class="feature-grid">
  <div class="feature-card">
    <h3>🧩 Modular Architecture</h3>
    <p>Easily swap components without changing other parts of the system. Want to switch from OpenAI to Anthropic? Just change the configuration.</p>
  </div>
  <div class="feature-card">
    <h3>🔌 Protocol-Based Design</h3>
    <p>Components communicate through well-defined interfaces, creating clean boundaries and enabling superior testing capabilities.</p>
  </div>
  <div class="feature-card">
    <h3>🔍 Complete Observability</h3>
    <p>Every component interaction is captured with transparent proxies, providing detailed runtime insights and automatic test case generation.</p>
  </div>
</div>

## What is Xaibo?

Xaibo is a powerful, protocol-driven framework that enables developers to build sophisticated AI agents with unprecedented flexibility and modularity. By using well-defined interfaces and dependency injection, Xaibo allows you to create, test, and deploy AI systems that are both robust and easily maintainable.

!!! tip "Quick Start"
    **Prerequisites:** Python 3.10 or higher installed
    
    Get up and running with Xaibo in minutes:
    ```bash
    pip install uv
    uvx xaibo init my_project
    cd my_project
    uv run xaibo dev
    ```
    Start with our [Getting Started guide](tutorial/index.md) guide to create your first Xaibo agent

## Why Choose Xaibo?

### 🧩 **Modular Architecture**
Easily swap components without changing other parts of the system. Want to switch from OpenAI to Anthropic? Just change the configuration.

### 🔌 **Protocol-Based Design**
Components communicate through well-defined interfaces, creating clean boundaries and enabling superior testing capabilities.

### 🔍 **Complete Observability**
Every component interaction is captured with transparent proxies, providing detailed runtime insights and automatic test case generation.

### 🚀 **Production Ready**
Built-in web server with OpenAI-compatible API and MCP (Model Context Protocol) support for seamless integration.

---

## Key Features

<div class="grid cards" markdown>

-   :material-puzzle-outline: **Protocol-Based Architecture**

    ---

    Components interact through well-defined protocol interfaces, creating clear boundaries and enabling easy testing with mocks.

-   :material-swap-horizontal: **Dependency Injection**

    ---

    Explicitly declare what components need, making it easy to swap implementations and inject predictable mocks for testing.

-   :material-eye-outline: **Transparent Proxies**

    ---

    Every component is wrapped with observability that captures parameters, timing, and exceptions for complete visibility.

-   :material-chart-timeline-variant: **Comprehensive Event System**

    ---

    Built-in event system provides real-time monitoring, call sequences tracking, and performance insights.

</div>

---

## Quick Navigation

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Getting Started](tutorial/index.md)**

    ---

    Step-by-step tutorial to build your first AI agent with tools and understand Xaibo's architecture

-   :material-book-open-page-variant: **[How-to Guides](how-to/index.md)**

    ---

    Practical guides for installation, tool integration, LLM configuration, and deployment

-   :material-brain: **[Core Concepts](explanation/index.md)**

    ---

    Deep dive into protocols, modules, dependency injection, and Xaibo's design principles

-   :material-api: **[API Reference](reference/index.md)**

    ---

    Complete technical documentation for modules, protocols, configuration, and CLI commands

-   :material-tools: **[Building Tools](tutorial/building-tools.md)**

    ---

    Learn to create custom Python and MCP tools that extend your agent's capabilities

-   :material-cog: **[Architecture Guide](explanation/architecture/protocols.md)**

    ---

    Understand Xaibo's protocol-based architecture and transparent proxy system

</div>

---

## Visual Debug Interface

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

---

## Community & Support

<div class="grid cards" markdown>

-   :fontawesome-brands-github: **[GitHub Repository](https://github.com/xpressai/xaibo)**

    ---

    Source code, issues, and contributions

-   :fontawesome-brands-discord: **[Discord Community](https://discord.gg/uASMzSSVKe)**

    ---

    Join our community for support and discussions

-   :material-email: **[Contact Us](mailto:hello@xpress.ai)**

    ---

    Get in touch with the Xaibo team

</div>

---

# Ready to Build?
Start with our [Getting Started guide](tutorial/index.md) to create your first Xaibo agent, or dive into [Core Concepts](explanation/index.md) to understand the framework's architecture.
