# How to deploy with OpenAI-compatible API

This guide shows you how to deploy your Xaibo agents as an OpenAI-compatible REST API, allowing any OpenAI client to interact with your agents.

!!! info "Available OpenAI Adapters"
    Xaibo provides two OpenAI-compatible adapters:
    
    - **[OpenAI API Adapter](../../reference/api/adapters.md#openaiapiadapter)** - Basic OpenAI Chat Completions API compatibility (covered in this guide)
    - **[OpenAI Responses Adapter](../../reference/api/openai-responses-adapter.md)** - Advanced response management with conversation history and persistence

## Install web server dependencies

Install the required web server dependencies:

```bash
pip install xaibo[webserver]
```

This includes FastAPI, Strawberry GraphQL, and other web server components.

## Deploy using the CLI

Use the built-in CLI for quick deployment:

```bash
# Deploy all agents in the agents directory
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --host 0.0.0.0 \
  --port 8000
```


## Test your deployment

Test the deployed API with curl:

```bash
# List available models (agents)
curl -X GET http://localhost:8000/openai/models

# Send a chat completion request
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-agent-id",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'

# Test streaming responses
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-agent-id",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true
  }'
```

## Use with OpenAI client libraries

Connect using official OpenAI client libraries:

### Python client
```python
# client_test.py
from openai import OpenAI

# Point to your Xaibo deployment
client = OpenAI(
    base_url="http://localhost:8000/openai",
    api_key="not-needed"  # Xaibo doesn't require API key by default
)

# List available models (your agents)
models = client.models.list()
print("Available agents:")
for model in models.data:
    print(f"  - {model.id}")

# Chat with an agent
response = client.chat.completions.create(
    model="your-agent-id",
    messages=[
        {"role": "user", "content": "What can you help me with?"}
    ]
)

print(response.choices[0].message.content)
```

### Node.js client
```javascript
// client_test.js
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'http://localhost:8000/openai',
  apiKey: 'not-needed'
});

async function testAgent() {
  // List available models
  const models = await openai.models.list();
  console.log('Available agents:', models.data.map(m => m.id));
  
  // Chat with an agent
  const completion = await openai.chat.completions.create({
    model: 'your-agent-id',
    messages: [
      { role: 'user', content: 'Hello from Node.js!' }
    ]
  });
  
  console.log(completion.choices[0].message.content);
}

testAgent().catch(console.error);
```

## Best practices

### Security
- Use HTTPS in production
- Implement API key authentication if needed
- Set up proper CORS policies
- Use environment variables for secrets

### Performance
- Use multiple workers for high load
- Implement connection pooling
- Cache agent configurations
- Monitor resource usage

### Reliability
- Add health checks and monitoring
- Implement graceful shutdown
- Use load balancers for redundancy
- Set up automated restarts

### Scaling
- Use container orchestration (Kubernetes, ECS)
- Implement horizontal pod autoscaling
- Monitor and optimize resource usage
- Use CDN for static assets

## Troubleshooting

### Port binding issues
- Check if port is already in use
- Verify firewall settings
- Use different port numbers for testing

### Agent loading errors
- Verify agent YAML syntax
- Check that all dependencies are installed
- Review agent configuration paths

### Performance problems
- Monitor CPU and memory usage
- Optimize agent configurations
- Use profiling tools to identify bottlenecks
- Consider scaling horizontally

### Connection issues
- Verify network connectivity
- Check DNS resolution
- Review proxy and load balancer settings
- Test with simple HTTP clients first