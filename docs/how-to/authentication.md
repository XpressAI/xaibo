# How to Set Up Authentication

This guide shows you how to secure your Xaibo server with API key authentication for both OpenAI and MCP adapters.

## Quick Start

The fastest way to add authentication:

1. **Set environment variables:**
   ```bash
   export CUSTOM_OPENAI_API_KEY="your-openai-secret-key"
   export MCP_API_KEY="your-mcp-secret-key"
   ```

2. **Start the server:**
   ```bash
   python -m xaibo.server.web --adapter xaibo.server.adapters.OpenAiApiAdapter --adapter xaibo.server.adapters.McpApiAdapter
   ```

3. **Test with curl:**
   ```bash
   curl -H "Authorization: Bearer your-openai-secret-key" http://localhost:8000/openai/models
   ```

## Step-by-Step Setup

### 1. Choose Your Authentication Method

**Option A: Environment Variables (Recommended)**
```bash
export CUSTOM_OPENAI_API_KEY="sk-your-secret-key-here"
export MCP_API_KEY="mcp-your-secret-key-here"
```

**Option B: Command Line Arguments**
```bash
python -m xaibo.server.web \
  --openai-api-key "sk-your-secret-key-here" \
  --mcp-api-key "mcp-your-secret-key-here" \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter
```

### 2. Start the Server with Adapters

**For OpenAI API only:**
```bash
python -m xaibo.server.web --adapter xaibo.server.adapters.OpenAiApiAdapter
```

**For MCP only:**
```bash
python -m xaibo.server.web --adapter xaibo.server.adapters.McpApiAdapter
```

**For both adapters:**
```bash
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter
```

### 3. Configure Your Agent Directory

```bash
python -m xaibo.server.web \
  --agent-dir ./my-agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter
```

## Testing Authentication

### Test OpenAI Adapter

**List available models:**
```bash
curl -H "Authorization: Bearer your-openai-secret-key" \
     http://localhost:8000/openai/models
```

**Send a chat completion:**
```bash
curl -X POST \
  -H "Authorization: Bearer your-openai-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-agent-name",
    "messages": [{"role": "user", "content": "Hello"}]
  }' \
  http://localhost:8000/openai/chat/completions
```

### Test MCP Adapter

**Initialize MCP connection:**
```bash
curl -X POST \
  -H "Authorization: Bearer your-mcp-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {}
    }
  }' \
  http://localhost:8000/mcp/
```

**List available tools:**
```bash
curl -X POST \
  -H "Authorization: Bearer your-mcp-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/list",
    "params": {}
  }' \
  http://localhost:8000/mcp/
```

## Common Issues

### "Missing Authorization header"
**Problem:** You forgot to include the Authorization header.

**Solution:** Add the header to your request:
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/openai/models
```

### "Invalid API key"
**Problem:** The API key doesn't match what the server expects.

**Solutions:**
- Check your environment variables: `echo $CUSTOM_OPENAI_API_KEY`
- Verify the key in your curl command matches exactly
- Restart the server after changing environment variables

### Server starts but authentication doesn't work
**Problem:** API key not configured properly.

**Solutions:**
- Make sure environment variables are set before starting the server
- Use command-line arguments instead: `--openai-api-key "your-key"`
- Check server logs for authentication errors

### MCP requests return HTTP 200 but with errors
**Problem:** This is normal - MCP uses JSON-RPC protocol.

**Solution:** Check the response body for error details:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "error": {
    "code": -32001,
    "message": "Invalid API key"
  }
}
```

## Security Notes

- **Keep API keys secret** - never commit them to version control
- **Use environment variables** for production deployments
- **Use strong, random keys** - consider using `openssl rand -hex 32`
- **Authentication is optional** - adapters work without API keys for development

## No Authentication Setup

To run without authentication (development only):

```bash
python -m xaibo.server.web \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --adapter xaibo.server.adapters.McpApiAdapter
```

Then test without Authorization headers:
```bash
curl http://localhost:8000/openai/models
```

## Related Guides

- [How to deploy with OpenAI-compatible API](deployment/openai-api.md) - Complete deployment guide with authentication examples
- [How to deploy as an MCP server](deployment/mcp-server.md) - MCP deployment with authentication setup
- [API Reference - Server Adapters](../reference/api/adapters.md) - Technical details about authentication implementation