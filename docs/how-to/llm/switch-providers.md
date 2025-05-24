# How to switch between different LLM providers

This guide shows you how to configure your Xaibo agents to use different LLM providers like OpenAI, Anthropic, Google, or AWS Bedrock.

## Switch to OpenAI models

1. Install the OpenAI dependency and configure your agent:

```bash
pip install xaibo[openai]
```

```yaml
# agents/openai_agent.yml
id: openai-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}  # Optional, uses env var by default
      temperature: 0.7
      max_tokens: 2000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your API key:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Available OpenAI models:
- `gpt-4` - Latest GPT-4 model
- `gpt-4-turbo` - Faster GPT-4 variant
- `gpt-3.5-turbo` - Cost-effective option
- `gpt-4o` - Optimized GPT-4 model

## Switch to Anthropic Claude

2. Install Anthropic dependencies and configure Claude:

```bash
pip install xaibo[anthropic]
```

```yaml
# agents/claude_agent.yml
id: claude-agent
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      model: claude-3-5-sonnet-20241022
      api_key: ${ANTHROPIC_API_KEY}
      temperature: 0.7
      max_tokens: 4000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Available Claude models:
- `claude-3-5-sonnet-20241022` - Latest Claude 3.5 Sonnet
- `claude-3-5-haiku-20241022` - Fast and efficient
- `claude-3-opus-20240229` - Most capable model
- `claude-3-sonnet-20240229` - Balanced performance

## Switch to Google Gemini

3. Install Google dependencies and configure Gemini:

```bash
pip install xaibo[google]
```

```yaml
# agents/gemini_agent.yml
id: gemini-agent
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: llm
    config:
      model: gemini-2.0-flash-001
      api_key: ${GOOGLE_API_KEY}
      temperature: 0.7
      max_tokens: 2000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your API key:

```bash
export GOOGLE_API_KEY=your_google_api_key_here
```

Available Gemini models:
- `gemini-2.0-flash-001` - Latest Gemini 2.0 Flash
- `gemini-1.5-pro` - High-capability model
- `gemini-1.5-flash` - Fast and efficient
- `gemini-pro` - Standard model

## Switch to AWS Bedrock

4. Install Bedrock dependencies and configure AWS models:

```bash
pip install xaibo[bedrock]
```

```yaml
# agents/bedrock_agent.yml
id: bedrock-agent
modules:
  - module: xaibo.primitives.modules.llm.BedrockLLM
    id: llm
    config:
      model: anthropic.claude-3-5-sonnet-20241022-v2:0
      region_name: us-east-1
      aws_access_key_id: ${AWS_ACCESS_KEY_ID}
      aws_secret_access_key: ${AWS_SECRET_ACCESS_KEY}
      temperature: 0.7
      max_tokens: 4000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=your_aws_access_key
export AWS_SECRET_ACCESS_KEY=your_aws_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Available Bedrock models:
- `anthropic.claude-3-5-sonnet-20241022-v2:0` - Claude 3.5 Sonnet
- `anthropic.claude-3-haiku-20240307-v1:0` - Claude 3 Haiku
- `amazon.titan-text-premier-v1:0` - Amazon Titan
- `meta.llama3-2-90b-instruct-v1:0` - Llama 3.2

## Use custom API endpoints

5. Configure custom endpoints for OpenAI-compatible APIs:

```yaml
# agents/custom_openai_agent.yml
id: custom-openai-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: your-custom-model
      base_url: https://your-custom-endpoint.com/v1
      api_key: ${CUSTOM_API_KEY}
      timeout: 120.0
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

This works with:
- Local LLM servers (Ollama, LM Studio)
- Azure OpenAI Service
- Custom OpenAI-compatible APIs

## Switch providers at runtime

6. Create agents that can use different providers dynamically:

```yaml
# agents/multi_provider_agent.yml
id: multi-provider-agent
modules:
  # Primary LLM
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: primary-llm
    config:
      model: gpt-4
      
  # Backup LLM
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: backup-llm
    config:
      model: claude-3-5-sonnet-20241022
      
  # LLM combinator to manage multiple providers
  - module: xaibo.primitives.modules.llm.LLMCombinator
    id: llm
    config:
      prompts:
        - "Use the primary model for this request"
        - "Use the backup model if primary fails"
        
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator

exchange:
  # Connect combinator to both LLMs
  - module: llm
    protocol: LLMProtocol
    provider: [primary-llm, backup-llm]
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
```

## Configure provider-specific parameters

7. Optimize settings for each provider:

### OpenAI configuration
```yaml
config:
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000
  top_p: 0.9
  frequency_penalty: 0.0
  presence_penalty: 0.0
  timeout: 60.0
```

### Anthropic configuration
```yaml
config:
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4000
  top_p: 0.9
  timeout: 60.0
```

### Google configuration
```yaml
config:
  model: gemini-2.0-flash-001
  temperature: 0.7
  max_tokens: 2000
  top_p: 0.9
  top_k: 40
```

### Bedrock configuration
```yaml
config:
  model: anthropic.claude-3-5-sonnet-20241022-v2:0
  region_name: us-east-1
  temperature: 0.7
  max_tokens: 4000
  top_p: 0.9
  timeout: 120.0
```

## Test different providers

8. Compare provider performance with the same prompt:

```bash
# Test OpenAI
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai-agent",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'

# Test Anthropic
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-agent", 
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'

# Test Google
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-agent",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'
```

## Handle provider-specific features

9. Configure features unique to each provider:

### Function calling support
```yaml
# OpenAI with function calling
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      supports_function_calling: true
      
# Anthropic with tool use
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      model: claude-3-5-sonnet-20241022
      supports_tool_use: true
```

### Vision capabilities
```yaml
# OpenAI with vision
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4-vision-preview
      supports_vision: true
      
# Google with multimodal
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: llm
    config:
      model: gemini-pro-vision
      supports_multimodal: true
```

## Monitor costs across providers

10. Track usage and costs for different providers:

```python
# cost_monitor.py
import os
from datetime import datetime

def log_llm_usage(provider, model, tokens_used, cost_estimate):
    """Log LLM usage for cost tracking"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "tokens": tokens_used,
        "estimated_cost": cost_estimate
    }
    
    with open("llm_usage.log", "a") as f:
        f.write(f"{log_entry}\n")

# Example usage tracking
providers_costs = {
    "openai": {"gpt-4": 0.03, "gpt-3.5-turbo": 0.002},
    "anthropic": {"claude-3-5-sonnet": 0.015, "claude-3-haiku": 0.0025},
    "google": {"gemini-pro": 0.0005, "gemini-flash": 0.000125},
    "bedrock": {"claude-3-sonnet": 0.015, "titan-text": 0.0008}
}
```

## Best practices

### Provider selection
- Choose based on your specific use case requirements
- Consider cost, performance, and feature needs
- Test multiple providers for critical applications

### Configuration management
- Use environment variables for API keys
- Store provider configs in separate files
- Version control your configurations

### Fallback strategies
- Configure backup providers for reliability
- Implement retry logic with exponential backoff
- Monitor provider availability and performance

### Security
- Rotate API keys regularly
- Use least-privilege access policies
- Monitor usage for anomalies

## Troubleshooting

### Authentication errors
- Verify API keys are correct and active
- Check account billing status and limits
- Ensure proper environment variable setup

### Model availability
- Verify model names match provider specifications
- Check regional availability for specific models
- Update to latest model versions when needed

### Rate limiting
- Implement proper retry logic with backoff
- Monitor usage against provider limits
- Consider upgrading to higher-tier plans

### Performance issues
- Adjust timeout values for slow responses
- Optimize prompt length and complexity
- Monitor token usage and costs