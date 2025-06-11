# Xaibo: The Modular AI Agent Framework

**Build flexible, observable, and production-ready AI agents with clean, swappable components.**

Xaibo is a modular framework designed to help you build sophisticated AI systems that are easy to test, debug, and evolve. Move beyond monolithic agent scripts and start creating with components you can trust.

<div style="display: flex; gap: 10px; margin: 20px 0;">
  <div style="flex: 1;">
    <img src="docs/images/sequence-diagram.png" alt="Xaibo Debug UI - Sequence Diagram Overview" width="100%">
    <p><em>Sequence Diagram Overview</em></p>
  </div>
  <div style="flex: 1;">
    <img src="docs/images/detail-view.png" alt="Xaibo Debug UI - Detail View" width="100%">
    <p><em>Detail View of Component Interactions</em></p>
  </div>
</div>

_Visually trace every step of your agent's operation in the debug UI._

## Why Use Xaibo?

### Build with Confidence, Not Concrete
Xaibo's protocol-driven architecture lets you define how components interact without locking you into specific
implementations. Swap LLMs, vector stores, or tools without rewriting your agent's core logic.

### Understand Your Agent's Every Thought
Every component is automatically wrapped in a transparent proxy that observes all inputs, outputs, and errors. The
built-in debug UI provides a sequence diagram of your agent's inner workings, making complex interactions easy to
understand and debug.

### Test, Don't Guess
With first-class support for dependency injection, you can easily swap in mock components to write fast, deterministic
tests for your agent's logic. Ensure your agent behaves as expected before you ever hit a real LLM API.


## Quick Start

Get your first Xaibo agent running in under a minute.

**Prerequisites:** Python 3.10+ and `pip`.

1.  **Install `uv`:** _(if you don't already have it)_

    ```bash
    pip install uv
    ```

2.  **Initialize a new project:**

    ```bash
    uvx xaibo init my-agent-project
    ```
    You will be asked what dependencies you want to install. That way you don't need to install half the internet, if you
    are going to use just third-party APIs.

3.  **Start the development server:**

    ```bash
    cd my-agent-project
    uv run xaibo dev
    ```
    This starts the development server with an OpenAI compatible chat completions API at `http://localhost:9001/openai`
    and the debugging ui at `http://localhost:9001`. 

4.  **Interact with the example agent:**
    You can now send requests to your agent using any OpenAI-compatible client.

    ```bash
    # Send a simple chat completion request to the Xaibo OpenAI-compatible API
    curl -X POST http://127.0.0.1:9001/openai/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "example",
        "messages": [
          {"role": "user", "content": "Hello, what time is it now?"}
        ]
      }'
    ```

    ```bash
    # Same request using HTTPie (a more user-friendly alternative to curl)
    http POST http://127.0.0.1:9001/openai/chat/completions \
      model=example \
      messages:='[{"role": "user", "content": "Hello, what time is it now?"}]'
    ```

### What You Get

The `init` command sets up a clean, organized project structure for you:

```
my-agent-project/
├── agents/
│   └── example.yml    # Your agent's configuration
├── modules/
│   └── __init__.py
├── tools/
│   └── example.py     # An example tool implementation
├── tests/
│   └── test_example.py
└── .env               # Environment variables
```

## Core Features

  * **Protocol-Driven Architecture:** Enforces clean separation between components.
  * **Built-in Debug UI:** Visually trace and inspect your agent's execution flow.
  * **Dependency Injection:** Easily swap implementations and write mockable, testable code.
  * **Extensible Module System:** Ships with modules for major LLM providers (OpenAI, Anthropic, Google), local embeddings, vector memory, and more.
  * **Tool Support:** Create tools with simple python, use MCP servers or integrate whatever fits your needs. 
  * **OpenAI-Compatible API:** Use your agent with a wide range of existing tools and libraries out-of-the-box.
  * **MCP Adapter:** Expose your agents as tools to any [Model Context Protocol](https://modelcontextprotocol.io/)-compatible client.

## Dive Deeper: Full Documentation

For detailed guides on agent configuration, core concepts, available protocol implementations, and creating your own
modules, please see our **[full documentation](https://xaibo.ai)**.

## Get Involved

Xaibo is actively developed and we welcome contributors!

  * **GitHub Repository:** [github.com/xpressai/xaibo](https://github.com/xpressai/xaibo) - Report issues, suggest features, or submit a pull request.
  * **Discord Community:** [Join our Discord Server](https://discord.gg/uASMzSSVKe) - Ask questions, share what you're building, and connect with the community.
  * **Contact Us:** hello@xpress.ai

## Development

### Roadmap

Xaibo is actively developing:
- Enhanced visual configuration UI
- Visual tool definition with Xircuits
- More API adapters beyond OpenAI standard
- Multi-user aware agents

The core principles and APIs are stable for production use.

### Contributing

#### Running Tests
Tests are implemented using pytest. If you are using PyCharm to run them, you 
will need to configure it to also show logging output. That way some failures
will be a lot easier to debug.

Go to File > Settings > Advanced Settings > Python and check the option 
`Pytest: do not add "--no-header --no-summary -q"`.