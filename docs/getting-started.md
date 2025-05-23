# Getting Started

Welcome to Xaibo! This guide will help you install Xaibo, create your first agent, and understand the basic workflow.

## Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- `pip` package manager
- Basic familiarity with YAML configuration files

!!! tip "Recommended: Use uv"
    We recommend using [uv](https://docs.astral.sh/uv/) for faster package management and project initialization.

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv if you don't have it
pip install uv

# Initialize a new Xaibo project
uvx xaibo init my_project

# Navigate to your project
cd my_project

# Start the development server
uv run xaibo dev
```

### Option 2: Using pip

```bash
# Install Xaibo with basic dependencies
pip install xaibo

# For web server and API functionality
pip install xaibo[webserver]

# For specific LLM providers
pip install xaibo[openai,anthropic,google]

# Install all dependencies
pip install xaibo[webserver,openai,anthropic,google,bedrock,local]
```

## Dependency Groups

Xaibo organizes dependencies into logical groups to keep the core package lightweight:

| Group | Purpose | Includes |
|-------|---------|----------|
| `webserver` | Web server and API adapters | fastapi, strawberry-graphql, watchfiles |
| `openai` | OpenAI integration | openai client library |
| `anthropic` | Anthropic Claude integration | anthropic client library |
| `google` | Google Gemini integration | google-genai client library |
| `bedrock` | AWS Bedrock integration | boto3 |
| `local` | Local embeddings and tokenization | sentence-transformers, tiktoken |
| `dev` | Development tools | coverage, devtools |

## Quick Start Tutorial

### Step 1: Initialize Your Project

When you run `uvx xaibo init my_project`, Xaibo creates this structure:

```
my_project/
├── agents/
│   └── example.yml    # Example agent configuration
├── modules/
│   └── __init__.py
├── tools/
│   ├── __init__.py
│   └── example.py     # Example tool implementation
├── tests/
│   └── test_example.py
└── .env               # Environment variables
```

### Step 2: Configure Your Environment

Edit the `.env` file to add your API keys:

```bash title=".env"
# OpenAI API Key (if using OpenAI models)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (if using Claude models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google API Key (if using Gemini models)
GOOGLE_API_KEY=your_google_api_key_here
```

### Step 3: Understand the Example Agent

The generated `agents/example.yml` demonstrates a complete agent configuration:

```yaml title="agents/example.yml"
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  - id: python-tools
    module: xaibo.primitives.modules.tools.PythonToolProvider
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.
```

This configuration defines:

- **LLM Module**: Uses OpenAI's GPT-3.5-turbo model
- **Tool Provider**: Loads Python tools from the `tools.example` package
- **Orchestrator**: Manages the agent's behavior and tool usage

### Step 4: Examine the Example Tool

The `tools/example.py` file shows how to create tools:

```python title="tools/example.py"
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
```

The `@tool` decorator automatically converts Python functions into tools that agents can use.

### Step 5: Start the Development Server

```bash
uv run xaibo dev
```

This starts:

- **Web Server**: Runs on `http://localhost:9001`
- **Debug UI**: Visual interface for monitoring agent operations
- **OpenAI-Compatible API**: Endpoint at `/openai/chat/completions`

### Step 6: Test Your Agent

#### Using curl

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Hello, what time is it now?"}
    ]
  }'
```

#### Using HTTPie (Alternative)

```bash
http POST http://127.0.0.1:9001/openai/chat/completions \
  model=example \
  messages:='[{"role": "user", "content": "Hello, what time is it now?"}]'
```

#### Expected Response

```json
{
  "id": "chat-12345",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "example",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The current time is 2024-01-15 14:30:25 UTC."
      },
      "finish_reason": "stop"
    }
  ]
}
```

## Debug UI Overview

Access the debug UI at `http://localhost:9001` to:

- **Monitor Agent Operations**: See real-time execution flow
- **View Component Interactions**: Understand how modules communicate
- **Debug Issues**: Inspect parameters, timing, and exceptions
- **Generate Test Cases**: Automatically create tests from production runs

## Next Steps

Now that you have Xaibo running, explore these areas:

!!! success "What's Next?"
    - **[Core Concepts](core-concepts.md)**: Understand protocols, modules, and exchanges
    - **[Features](features.md)**: Explore advanced capabilities
    - **[Project Structure](project-structure.md)**: Learn about organizing larger projects

## Common Issues

### API Key Not Found

If you see authentication errors:

1. Ensure your API key is set in the `.env` file
2. Restart the development server after adding environment variables
3. Check that the key has the correct permissions

### Module Import Errors

If tools aren't loading:

1. Verify the `tool_packages` path in your agent configuration
2. Ensure `__init__.py` files exist in your tool directories
3. Check that the `@tool` decorator is imported correctly

### Port Already in Use

If port 9001 is busy:

```bash
# Use a different port
uv run xaibo dev --port 9002
```

## Getting Help

- **Documentation**: Continue reading the [Core Concepts](core-concepts.md)
- **Community**: Join our [Discord](https://discord.gg/uASMzSSVKe)
- **Issues**: Report bugs on [GitHub](https://github.com/xpressai/xaibo)
- **Email**: Contact us at [hello@xpress.ai](mailto:hello@xpress.ai)