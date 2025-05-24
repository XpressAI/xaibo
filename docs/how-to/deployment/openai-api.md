# How to deploy with OpenAI-compatible API

This guide shows you how to deploy your Xaibo agents as an OpenAI-compatible REST API, allowing any OpenAI client to interact with your agents.

## Install web server dependencies

1. Install the required web server dependencies:

```bash
pip install xaibo[webserver]
```

This includes FastAPI, Strawberry GraphQL, and other web server components.

## Create a basic deployment script

2. Create a deployment script for your agents:

```python
# deploy.py
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter

def main():
    # Initialize Xaibo
    xaibo = Xaibo()
    
    # Register your agents from the agents directory
    xaibo.register_agents_from_directory("./agents")
    
    # Create web server with OpenAI adapter
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[OpenAiApiAdapter(xaibo)]
    )
    
    # Start the server
    server.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

## Deploy using the CLI

3. Use the built-in CLI for quick deployment:

```bash
# Deploy all agents in the agents directory
python -m xaibo.server.web \
  --agent-dir ./agents \
  --adapter xaibo.server.adapters.OpenAiApiAdapter \
  --host 0.0.0.0 \
  --port 8000
```

## Configure environment variables

4. Set up environment variables for your deployment:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Server configuration
XAIBO_HOST=0.0.0.0
XAIBO_PORT=8000
XAIBO_LOG_LEVEL=INFO

# Optional: Custom base path
XAIBO_BASE_PATH=/api/v1
```

Load environment variables in your deployment:

```python
# deploy.py
import os
from dotenv import load_dotenv
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter

def main():
    # Load environment variables
    load_dotenv()
    
    xaibo = Xaibo()
    xaibo.register_agents_from_directory("./agents")
    
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[OpenAiApiAdapter(xaibo)]
    )
    
    # Use environment variables for configuration
    host = os.getenv("XAIBO_HOST", "127.0.0.1")
    port = int(os.getenv("XAIBO_PORT", "8000"))
    
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()
```

## Test your deployment

5. Test the deployed API with curl:

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

6. Connect using official OpenAI client libraries:

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

## Deploy with Docker

7. Create a Docker deployment:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "deploy.py"]
```

```txt
# requirements.txt
xaibo[webserver,openai,anthropic]
python-dotenv
```

Build and run the container:

```bash
# Build the image
docker build -t xaibo-api .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -v $(pwd)/agents:/app/agents \
  xaibo-api
```

## Deploy with Docker Compose

8. Use Docker Compose for multi-service deployment:

```yaml
# docker-compose.yml
version: '3.8'

services:
  xaibo-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - XAIBO_HOST=0.0.0.0
      - XAIBO_PORT=8000
    volumes:
      - ./agents:/app/agents
      - ./memory_storage:/app/memory_storage
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - xaibo-api
    restart: unless-stopped
```

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream xaibo {
        server xaibo-api:8000;
    }
    
    server {
        listen 80;
        server_name your-domain.com;
        
        location / {
            proxy_pass http://xaibo;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

Start the services:

```bash
docker-compose up -d
```

## Deploy to cloud platforms

9. Deploy to various cloud platforms:

### AWS ECS
```json
{
  "family": "xaibo-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "xaibo-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/xaibo-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-key-here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/xaibo-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: xaibo-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
      - image: gcr.io/your-project/xaibo-api
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          value: "your-key-here"
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
```

Deploy to Cloud Run:

```bash
# Build and push image
gcloud builds submit --tag gcr.io/your-project/xaibo-api

# Deploy service
gcloud run deploy xaibo-api \
  --image gcr.io/your-project/xaibo-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Heroku
```yaml
# heroku.yml
build:
  docker:
    web: Dockerfile
run:
  web: python deploy.py
```

```bash
# Deploy to Heroku
heroku create your-xaibo-app
heroku stack:set container
heroku config:set OPENAI_API_KEY=your_key_here
git push heroku main
```

## Configure load balancing

10. Set up load balancing for high availability:

```python
# deploy_cluster.py
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter
import multiprocessing
import uvicorn

def create_app():
    xaibo = Xaibo()
    xaibo.register_agents_from_directory("./agents")
    
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[OpenAiApiAdapter(xaibo)]
    )
    
    return server.app

def main():
    # Run with multiple workers
    uvicorn.run(
        "deploy_cluster:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        workers=multiprocessing.cpu_count()
    )

if __name__ == "__main__":
    main()
```

## Monitor your deployment

11. Add monitoring and health checks:

```python
# deploy_monitored.py
import logging
import time
from xaibo import Xaibo
from xaibo.server import XaiboWebServer
from xaibo.server.adapters.openai import OpenAiApiAdapter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_monitored_app():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    xaibo = Xaibo()
    xaibo.register_agents_from_directory("./agents")
    
    server = XaiboWebServer(
        xaibo=xaibo,
        adapters=[OpenAiApiAdapter(xaibo)]
    )
    
    app = server.app
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "agents": list(xaibo.agents.keys())
        }
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return {
            "total_agents": len(xaibo.agents),
            "uptime": time.time() - start_time
        }
    
    return app

start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_monitored_app(), host="0.0.0.0", port=8000)
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