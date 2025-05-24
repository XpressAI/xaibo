# LLM Modules Reference

LLM modules provide implementations of the [`LLMProtocol`](../protocols/llm.md) for various language model providers. Each module handles provider-specific authentication, request formatting, and response parsing.

## OpenAILLM

OpenAI language model integration supporting GPT models.

**Source**: [`src/xaibo/primitives/modules/llm/openai.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/openai.py)

**Module Path**: `xaibo.primitives.modules.llm.OpenAILLM`

**Dependencies**: `openai` dependency group

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | Required | OpenAI model name (e.g., "gpt-4", "gpt-3.5-turbo") |
| `api_key` | `str` | `None` | OpenAI API key (falls back to `OPENAI_API_KEY` env var) |
| `base_url` | `str` | `"https://api.openai.com/v1"` | Base URL for OpenAI API |
| `timeout` | `float` | `60.0` | Request timeout in seconds |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate |
| `top_p` | `float` | `None` | Default nucleus sampling parameter |

### Supported Models

| Model Family | Model Names | Context Length |
|--------------|-------------|----------------|
| GPT-4 | `gpt-4`, `gpt-4-turbo`, `gpt-4o` | 128K tokens |
| GPT-3.5 | `gpt-3.5-turbo` | 16K tokens |
| GPT-4 Mini | `gpt-4o-mini` | 128K tokens |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: openai-llm
    config:
      model: gpt-4
      api_key: sk-...  # Optional, uses OPENAI_API_KEY env var
      temperature: 0.7
      max_tokens: 2048
      timeout: 30.0
```

### Features

- **Function Calling**: Full support for OpenAI function calling
- **Vision**: Image input support for vision-capable models
- **Streaming**: Real-time response streaming
- **Token Usage**: Detailed token consumption tracking

## AnthropicLLM

Anthropic Claude model integration.

**Source**: [`src/xaibo/primitives/modules/llm/anthropic.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/anthropic.py)

**Module Path**: `xaibo.primitives.modules.llm.AnthropicLLM`

**Dependencies**: `anthropic` dependency group

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | Required | Anthropic model name |
| `api_key` | `str` | `None` | Anthropic API key (falls back to `ANTHROPIC_API_KEY` env var) |
| `base_url` | `str` | `None` | Custom base URL for Anthropic API |
| `timeout` | `float` | `60.0` | Request timeout in seconds |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate |

### Supported Models

| Model | Context Length | Description |
|-------|----------------|-------------|
| `claude-3-5-sonnet-20241022` | 200K tokens | Latest Claude 3.5 Sonnet |
| `claude-3-5-haiku-20241022` | 200K tokens | Latest Claude 3.5 Haiku |
| `claude-3-opus-20240229` | 200K tokens | Claude 3 Opus |
| `claude-3-sonnet-20240229` | 200K tokens | Claude 3 Sonnet |
| `claude-3-haiku-20240307` | 200K tokens | Claude 3 Haiku |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: claude-llm
    config:
      model: claude-3-5-sonnet-20241022
      temperature: 0.7
      max_tokens: 4096
```

### Features

- **Tool Use**: Native support for Anthropic tool use
- **Vision**: Image analysis capabilities
- **Streaming**: Real-time response streaming
- **System Messages**: Dedicated system message handling

## GoogleLLM

Google Gemini model integration with Vertex AI support.

**Source**: [`src/xaibo/primitives/modules/llm/google.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/google.py)

**Module Path**: `xaibo.primitives.modules.llm.GoogleLLM`

**Dependencies**: `google` dependency group

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | Required | Google model name |
| `api_key` | `str` | `None` | Google API key (for AI Studio) |
| `vertexai` | `bool` | `False` | Use Vertex AI instead of AI Studio |
| `project` | `str` | `None` | GCP project ID (required for Vertex AI) |
| `location` | `str` | `"us-central1"` | Vertex AI location |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate |

### Supported Models

| Model | Context Length | Description |
|-------|----------------|-------------|
| `gemini-2.0-flash-exp` | 1M tokens | Latest experimental Gemini 2.0 |
| `gemini-1.5-pro` | 2M tokens | Gemini 1.5 Pro |
| `gemini-1.5-flash` | 1M tokens | Gemini 1.5 Flash |
| `gemini-1.0-pro` | 32K tokens | Gemini 1.0 Pro |

### Example Configuration

```yaml
# AI Studio (API key)
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: gemini-llm
    config:
      model: gemini-1.5-pro
      api_key: AIza...
      temperature: 0.7

# Vertex AI (service account)
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: gemini-vertex
    config:
      model: gemini-1.5-pro
      vertexai: true
      project: my-gcp-project
      location: us-central1
```

### Features

- **Multimodal**: Native support for text, images, audio, and video
- **Function Calling**: Google function calling support
- **Streaming**: Real-time response streaming
- **Safety Settings**: Configurable content safety filters

## BedrockLLM

AWS Bedrock model integration supporting multiple providers.

**Source**: [`src/xaibo/primitives/modules/llm/bedrock.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/bedrock.py)

**Module Path**: `xaibo.primitives.modules.llm.BedrockLLM`

**Dependencies**: `bedrock` dependency group

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"anthropic.claude-v2"` | Bedrock model ID |
| `region_name` | `str` | `"us-east-1"` | AWS region |
| `aws_access_key_id` | `str` | `None` | AWS access key (optional) |
| `aws_secret_access_key` | `str` | `None` | AWS secret key (optional) |
| `timeout` | `float` | `60.0` | Request timeout in seconds |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate |

### Supported Models

| Provider | Model ID | Description |
|----------|----------|-------------|
| Anthropic | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Claude 3.5 Sonnet |
| Anthropic | `anthropic.claude-3-haiku-20240307-v1:0` | Claude 3 Haiku |
| Amazon | `amazon.titan-text-premier-v1:0` | Titan Text Premier |
| Meta | `meta.llama3-2-90b-instruct-v1:0` | Llama 3.2 90B |
| Mistral | `mistral.mistral-large-2407-v1:0` | Mistral Large |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.BedrockLLM
    id: bedrock-llm
    config:
      model: anthropic.claude-3-5-sonnet-20241022-v2:0
      region_name: us-west-2
      temperature: 0.7
      max_tokens: 4096
```

### Features

- **Multi-Provider**: Access to multiple model providers through Bedrock
- **AWS Integration**: Native AWS authentication and billing
- **Streaming**: Real-time response streaming
- **Regional Deployment**: Deploy in multiple AWS regions

## LLMCombinator

Combines multiple LLM instances for advanced workflows.

**Source**: [`src/xaibo/primitives/modules/llm/combinator.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/combinator.py)

**Module Path**: `xaibo.primitives.modules.llm.LLMCombinator`

**Dependencies**: None

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md), Uses [`LLMProtocol`](../protocols/llm.md) (list)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompts` | `List[str]` | `[]` | Specialized prompts for each LLM |

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llms` | `List[LLMProtocol]` | List of LLM instances to combine |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: gpt4
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: claude
    config:
      model: claude-3-5-sonnet-20241022
  
  - module: xaibo.primitives.modules.llm.LLMCombinator
    id: combined-llm
    config:
      prompts:
        - "You are a creative writing assistant."
        - "You are a technical analysis expert."

exchange:
  - module: combined-llm
    protocol: LLMProtocol
    provider: [gpt4, claude]
```

### Features

- **Multi-Model**: Combine responses from multiple models
- **Specialized Prompts**: Different system prompts for each model
- **Response Merging**: Automatic merging of multiple responses
- **Fallback**: Automatic fallback if one model fails

## MockLLM

Mock LLM implementation for testing and development.

**Source**: [`src/xaibo/primitives/modules/llm/mock.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/mock.py)

**Module Path**: `xaibo.primitives.modules.llm.MockLLM`

**Dependencies**: None

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `responses` | `List[str]` | `[]` | Predefined responses to return |
| `streaming_delay` | `int` | `0` | Delay between streaming chunks (ms) |
| `streaming_chunk_size` | `int` | `3` | Characters per streaming chunk |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: mock-llm
    config:
      responses:
        - "This is the first mock response."
        - "This is the second mock response."
        - "This is the third mock response."
      streaming_delay: 50
      streaming_chunk_size: 5
```

### Features

- **Deterministic**: Predictable responses for testing
- **Cycling**: Cycles through responses list
- **Streaming Simulation**: Simulates streaming with configurable delays
- **No Dependencies**: No external API dependencies

## RelayLLM

Relay LLM requests to another LLM with modifications.

**Source**: [`src/xaibo/primitives/modules/llm/relay.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/relay.py)

**Module Path**: `xaibo.primitives.modules.llm.RelayLLM`

**Dependencies**: None

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md), Uses [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system_prompt_override` | `str` | `None` | Override system prompt |
| `temperature_override` | `float` | `None` | Override temperature |
| `max_tokens_override` | `int` | `None` | Override max tokens |

### Constructor Dependencies

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `LLMProtocol` | Target LLM to relay requests to |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: base-llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.llm.RelayLLM
    id: specialized-llm
    config:
      system_prompt_override: "You are a specialized coding assistant."
      temperature_override: 0.1

exchange:
  - module: specialized-llm
    protocol: LLMProtocol
    provider: base-llm
```

### Features

- **Request Modification**: Modify requests before forwarding
- **Response Passthrough**: Forward responses unchanged
- **Parameter Override**: Override specific parameters
- **Transparent Relay**: Maintains full LLM protocol compatibility

## Common Configuration Patterns

### Environment-Based Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: ${OPENAI_MODEL:-gpt-3.5-turbo}
      temperature: ${TEMPERATURE:-0.7}
      max_tokens: ${MAX_TOKENS:-2048}
```

### Multi-Provider Fallback

```yaml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: primary-llm
    config:
      model: gpt-4
  
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: fallback-llm
    config:
      model: claude-3-5-sonnet-20241022
  
  - module: xaibo.primitives.modules.llm.LLMCombinator
    id: resilient-llm
    config:
      prompts: ["", ""]  # Same prompt for both

exchange:
  - module: resilient-llm
    protocol: LLMProtocol
    provider: [primary-llm, fallback-llm]
```

### Development vs Production

```yaml
# Development
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: llm
    config:
      responses: ["Development response"]

# Production
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
```

## Error Handling

All LLM modules handle common error scenarios:

### Authentication Errors

```python
# Missing API key
LLMAuthenticationError: "API key not provided and OPENAI_API_KEY not set"

# Invalid API key
LLMAuthenticationError: "Invalid API key provided"
```

### Rate Limiting

```python
# Rate limit exceeded
LLMRateLimitError: "Rate limit exceeded. Retry after 60 seconds"
```

### Model Errors

```python
# Model not found
LLMModelNotFoundError: "Model 'invalid-model' not found"

# Context length exceeded
LLMError: "Request exceeds maximum context length of 4096 tokens"
```

### Network Errors

```python
# Timeout
LLMError: "Request timed out after 60 seconds"

# Connection error
LLMError: "Failed to connect to API endpoint"
```

## Performance Considerations

### Request Optimization

1. **Batch Requests**: Use multiple messages in single request when possible
2. **Context Management**: Trim conversation history to stay within limits
3. **Streaming**: Use streaming for long responses to improve perceived performance
4. **Caching**: Cache responses for identical requests

### Resource Management

1. **Connection Pooling**: Reuse HTTP connections
2. **Rate Limiting**: Implement client-side rate limiting
3. **Timeout Configuration**: Set appropriate timeouts for your use case
4. **Memory Usage**: Monitor memory usage for large conversations

### Cost Optimization

1. **Model Selection**: Choose appropriate model for task complexity
2. **Token Management**: Monitor and optimize token usage
3. **Request Batching**: Combine multiple operations when possible
4. **Prompt Engineering**: Optimize prompts for efficiency