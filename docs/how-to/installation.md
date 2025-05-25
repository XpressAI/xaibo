# How to install Xaibo with different dependency groups

This guide shows you how to install Xaibo with only the dependencies you need for your specific use case.

## Prerequisites

Before installing Xaibo, ensure you have:
- Python 3.10 or higher installed
- pip or uv package manager

## Install core Xaibo package

Install the minimal Xaibo package without optional dependencies:

```bash
pip install xaibo
```

This gives you the core framework with basic functionality.

## Install with specific LLM providers

### OpenAI models (GPT-3.5, GPT-4)

```bash
pip install xaibo[openai]
```

### Anthropic Claude models

```bash
pip install xaibo[anthropic]
```

### Google Gemini models

```bash
pip install xaibo[google]
```

### AWS Bedrock models

```bash
pip install xaibo[bedrock]
```

### Multiple LLM providers

```bash
pip install xaibo[openai,anthropic,google]
```

## Install with web server capabilities

For running the debug UI and API endpoints:

```bash
pip install xaibo[webserver]
```

This includes FastAPI, Strawberry GraphQL, and other web dependencies.

## Install with local AI capabilities

For local embeddings, tokenization, and transformers:

```bash
pip install xaibo[local]
```

This includes sentence-transformers, tiktoken, and Hugging Face transformers.

## Install everything

For full functionality with all optional dependencies:

```bash
pip install xaibo[webserver,openai,anthropic,google,bedrock,local]
```

## Install for development

If you're contributing to Xaibo or need development tools:

```bash
pip install xaibo[dev]
```

This includes coverage tools and development utilities.

## Using uv (recommended)

For faster installation and better dependency resolution, use [`uv`](https://docs.astral.sh/uv/):

```bash
# Install uv first
pip install uv

# Install Xaibo with uv
uv add xaibo[openai,webserver]
```

## Verify installation

Test your installation by checking the version:

```bash
python -c "import xaibo; print(xaibo.__version__)"
```

Or use the CLI:

```bash
xaibo --version
```

## Quick start after installation

Initialize a new project to test your installation:

```bash
# Create a new project
uvx xaibo init my_test_project

# Navigate to the project
cd my_test_project

# Start the development server
uv run xaibo dev
```

Visit `http://localhost:9001` to see the debug UI and confirm everything is working.

## Troubleshooting

### Import errors for optional dependencies

If you get import errors like `ModuleNotFoundError: No module named 'openai'`, install the missing dependency group:

```bash
pip install xaibo[openai]
```

### Version conflicts

If you encounter dependency conflicts, try using uv which has better dependency resolution:

```bash
uv add xaibo[your,dependencies,here]
```

### Virtual environment issues

Always install Xaibo in a virtual environment to avoid conflicts:

```bash
python -m venv xaibo-env
source xaibo-env/bin/activate  # On Windows: xaibo-env\Scripts\activate
pip install xaibo[your,dependencies]
```