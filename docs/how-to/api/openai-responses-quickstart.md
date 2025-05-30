# How to Start the OpenAI Responses API

Get the OpenAI Responses API running in 2 minutes with the simplest possible setup.

## Prerequisites

You need:

- Xaibo installed with webserver support: `pip install xaibo[webserver]`
- At least one agent configuration in an [`./agents/`](../../tutorial/getting-started.md) directory

## Start the Server

Run this single command:

```bash
python -m xaibo.server.web --adapter xaibo.server.adapters.openai_responses.OpenAiResponsesApiAdapter
```

The server starts on [`http://localhost:8000`](http://localhost:8000) and automatically:

- Loads all agents from [`./agents/`](../../tutorial/getting-started.md)
- Creates a `./responses/` directory for response storage
- Initializes a SQLite database for persistence

## Test the API

Make your first request:

```bash
curl -X POST http://localhost:8000/openai/responses \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, how are you today?",
    "model": "example"
  }'
```

Replace `"example"` with your actual agent ID from your [`agents/`](../../tutorial/getting-started.md) directory.

### Expected Response

You'll get a JSON response like this:

```json
{
  "id": "resp_abc123",
  "object": "response", 
  "status": "completed",
  "model": "example",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Hello! I'm doing well, thank you for asking...",
          "annotations": []
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 12,
    "output_tokens": 18,
    "total_tokens": 30
  }
}
```

## What's Next

Your API is now running! Here are your next steps:

- **API Reference**: See the complete [OpenAI Responses Adapter documentation](../../reference/api/openai-responses-adapter.md) for all endpoints, parameters, and response formats
- **Advanced Deployment**: Learn about [OpenAI-compatible API deployment](../deployment/openai-api.md) for production setups
- **Agent Configuration**: Review [agent configuration](../../reference/agent-config.md) to customize your agents
- **Troubleshooting**: Check the [troubleshooting guide](../../reference/troubleshooting.md) if you encounter issues