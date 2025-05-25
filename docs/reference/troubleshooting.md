# Troubleshooting Reference

This reference provides systematic solutions for common issues encountered when using Xaibo. Each section describes specific problems, their symptoms, and step-by-step resolution procedures.

## Installation Issues

### Missing Dependencies Error

**Symptoms:**

- `ImportError` when importing xaibo modules
- `ModuleNotFoundError` for optional dependencies
- CLI commands fail with import errors

**Causes:**

- Missing optional dependency groups
- Incomplete installation
- Python version incompatibility

**Resolution:**

1. Verify Python version: `python --version` (requires >=3.10)
2. Install with required dependency groups:
   ```bash
   pip install xaibo[webserver,openai,anthropic]
   ```
3. For development installations:
   ```bash
   pip install -e .[webserver,openai,anthropic]
   ```

**Available dependency groups:**

- `webserver`: FastAPI, Strawberry GraphQL, watchfiles
- `openai`: OpenAI client library
- `anthropic`: Anthropic client library  
- `google`: Google GenAI library
- `bedrock`: AWS Boto3 for Bedrock
- `local`: Sentence transformers, tiktoken, transformers

### UV Package Manager Issues

**Symptoms:**

- `xaibo init` command fails
- `FileNotFoundError` for uv command
- Project initialization incomplete

**Resolution:**

1. Install UV package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Verify UV installation: `uv --version`
3. Ensure UV is in PATH
4. Retry project initialization


### Web Server Dependencies Missing

**Symptoms:**

- `ImportError: cannot import name 'XaiboWebServer'`
- `xaibo dev` or `xaibo serve` commands fail

**Resolution:**

1. Install webserver dependencies:
   ```bash
   pip install xaibo[webserver]
   ```
2. Verify FastAPI installation: `python -c "import fastapi"`

## Configuration Problems

### Invalid Agent Configuration

**Symptoms:**

- `ValueError: Invalid agent config`
- YAML parsing errors
- Agent instantiation failures

**Common causes and fixes:**

**Missing required fields:**
```yaml
# Incorrect - missing id
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM

# Correct
id: my-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
```

**Invalid module paths:**
```yaml
# Incorrect - wrong module path
modules:
  - module: xaibo.llm.OpenAI
    id: llm

# Correct
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
```

**Missing exchange configuration:**
```yaml
# May require explicit exchange config for ambiguous protocols
exchange:
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
```

### Multiple Provider Conflicts

**Symptoms:**

- `ValueError: Multiple providers found for protocol`
- Agent configuration validation errors

**Resolution:**

1. Identify conflicting providers in error message
2. Add explicit exchange configuration:
   ```yaml
   exchange:
     - module: target_module_id
       protocol: ConflictingProtocol
       provider: preferred_provider_id
   ```
3. Remove unused provider modules if not needed

### Environment Variable Issues

**Symptoms:**

- Authentication errors with LLM providers
- `401 Unauthorized` responses
- Missing API key errors

**Resolution:**

1. Create `.env` file in project root:
   ```bash
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   AWS_ACCESS_KEY_ID=your_key_here
   AWS_SECRET_ACCESS_KEY=your_key_here
   ```
2. Verify environment loading in code:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## Runtime Errors

### Module Import Failures

**Symptoms:**

- `ImportError` during agent instantiation
- `AttributeError: module has no attribute`
- Module class not found errors

**Resolution:**

1. Verify module path in configuration:
   ```python
   # Test module import manually
   from xaibo.primitives.modules.llm import OpenAILLM
   ```
2. Check for typos in module names
3. Ensure all required dependencies are installed
4. Verify Python path includes project directory

### Protocol Implementation Errors

**Symptoms:**

- `AttributeError: Entry module does not implement TextMessageHandlerProtocol`
- Missing protocol method errors
- Protocol mismatch exceptions

**Resolution:**

1. Verify module implements required protocols:
   ```python
   # Check module provides correct protocols
   module.provides = ["TextMessageHandlerProtocol"]
   ```
2. Ensure protocol methods are implemented:
   ```python
   async def handle_text(self, text: str):
       # Implementation required
   ```
3. Check exchange configuration maps protocols correctly


### Tool Integration Failures

**Symptoms:**

- Tool discovery errors
- Function call execution failures
- MCP server connection issues

**Python tool errors:**

1. Verify tool package structure:
   ```python
   # tools/__init__.py must exist
   # tools/example.py with @tool decorator
   from xaibo.primitives.modules.tools.python_tool_provider import tool
   
   @tool
   def my_function():
       """Function description"""
       return "result"
   ```

2. Check tool package configuration:
   ```yaml
   config:
     tool_packages: [tools.example]  # Correct import path
   ```

**MCP server errors:**

1. Verify server process is running
2. Check connection configuration:
   ```yaml
   config:
     servers:
       - name: my-server
         command: ["python", "server.py"]
         args: []
   ```
3. Test server connectivity manually

## Integration Problems

### LLM Provider Issues

**OpenAI Integration:**

- Verify API key format: `sk-...`
- Check model availability
- Monitor rate limits and quotas

**Anthropic Integration:**

- Verify API key format: `sk-ant-...`
- Check model names
- Handle content filtering responses

**Google Integration:**

- Verify API key configuration
- Check model availability
- Handle safety filter responses

**AWS Bedrock Integration:**

- Configure AWS credentials properly
- Verify region availability
- Check model access permissions

### MCP Server Integration

**Connection Issues:**

- Verify server executable permissions
- Check server startup logs
- Test server independently
- Validate JSON-RPC communication

**Protocol Compatibility:**

- Ensure MCP protocol version compatibility
- Verify tool schema definitions
- Check resource URI formats