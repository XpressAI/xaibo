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
# Deploy all agents in the agents directory (no authentication)
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --host 0.0.0.0 \
  --port 8000

# Deploy with API key authentication
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --host 0.0.0.0 \
  --port 8000 \
  --openai-api-key sk-your-secret-key-here
```


## Test your deployment

Test the deployed API with curl:

### Without Authentication

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

### With Authentication

```bash
# List available models (agents) with API key
curl -X GET http://localhost:8000/openai/models \
  -H "Authorization: Bearer sk-your-secret-key-here"

# Send a chat completion request with API key
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-secret-key-here" \
  -d '{
    "model": "your-agent-id",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'

# Test streaming responses with API key
curl -X POST http://localhost:8000/openai/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-secret-key-here" \
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

#### Without Authentication
```python
# client_test.py
from openai import OpenAI

# Point to your Xaibo deployment (no authentication)
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
API_
print(response.choices[0].message.content)
```

#### With Authentication
```python
# client_test_auth.py
from openai import OpenAI

# Point to your Xaibo deployment (with authentication)
client = OpenAI(
    base_url="http://localhost:8000/openai",
    api_key="sk-your-secret-key-here"  # Use your configured API key
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

#### Without Authentication
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

#### With Authentication
```javascript
// client_test_auth.js
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'http://localhost:8000/openai',
  apiKey: 'sk-your-secret-key-here'  // Use your configured API key
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

## API Key Configuration

!!! tip "Detailed Authentication Setup"
    For comprehensive authentication setup including troubleshooting and security best practices, see the [authentication guide](../authentication.md).

### Environment Variables

The recommended approach is to use environment variables for API key configuration:

```bash
# Set environment variable
export CUSTOM_OPENAI_API_KEY="sk-your-secret-key-here"

# Start server (API key automatically detected)
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --host 0.0.0.0 \
  --port 8000
```

### Command Line Arguments

Alternatively, provide API keys via command line arguments:

```bash
# API key via command line (overrides environment variable)
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --host 0.0.0.0 \
  --port 8000 \
  --openai-api-key sk-your-secret-key-here
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Use environment variable for API key
ENV CUSTOM_OPENAI_API_KEY=""

CMD ["python", "-m", "xaibo.server.web", \
     "--agent-dir", "./agents", \
     "--adapter", "xaibo.server.adapters.OpenAiApiAdapter", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
```

```bash
# Run with Docker
docker run -e CUSTOM_OPENAI_API_KEY=sk-your-secret-key-here -p 8000:8000 your-xaibo-image
```

## Best practices

### Security
- Use HTTPS in production
- Always use API key authentication in production environments
- Set up proper CORS policies
- Use environment variables for secrets
- Rotate API keys regularly
- Monitor API key usage for unusual patterns

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