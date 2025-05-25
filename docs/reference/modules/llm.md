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
| `model` | `str` | `"gpt-4.1-nano"` | OpenAI model name (e.g., "gpt-4", "gpt-4.1-nano") |
| `api_key` | `str` | `None` | OpenAI API key (falls back to `OPENAI_API_KEY` env var) |
| `base_url` | `str` | `"https://api.openai.com/v1"` | Base URL for OpenAI API |
| `timeout` | `float` | `60.0` | Request timeout in seconds |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate |
| `top_p` | `float` | `None` | Default nucleus sampling parameter |

**Note**: Additional configuration keys become default_kwargs and are passed to the OpenAI API.


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

- **Function Calling**: Full support for OpenAI function calling with automatic Python type to JSON Schema mapping
- **Vision**: Image input support for vision-capable models
- **Streaming**: Real-time response streaming
- **Token Usage**: Detailed token consumption tracking

### Implementation Details

#### Function Type Mapping

The [`_prepare_functions`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/openai.py:114) method automatically maps Python types to JSON Schema types:

- `str` → `string`
- `int` → `integer`
- `float` → `number`
- `bool` → `boolean`
- `list` → `array`
- `dict` → `object`
- `None` → `null`

This ensures proper type validation in OpenAI function calling.

### OpenAI API Compatibility

[`OpenAILLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/openai.py) can be used with any OpenAI API-compatible provider by configuring the `base_url` parameter:

- **Cloud Providers**: SambaNova, Together AI, Groq, and other hosted services
- **Local Inference**: Ollama, LM Studio, vLLM, and other local servers
- **Self-Hosted**: Custom OpenAI-compatible API implementations

Configure the `base_url` to point to your provider's endpoint while keeping the same OpenAI client interface and authentication patterns.

## AnthropicLLM

Anthropic Claude model integration.

**Source**: [`src/xaibo/primitives/modules/llm/anthropic.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/anthropic.py)

**Module Path**: `xaibo.primitives.modules.llm.AnthropicLLM`

**Dependencies**: `anthropic` dependency group

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"claude-3-opus-20240229"` | Anthropic model name |
| `api_key` | `str` | `None` | Anthropic API key (falls back to `ANTHROPIC_API_KEY` env var) |
| `base_url` | `str` | `None` | Custom base URL for Anthropic API |
| `timeout` | `float` | `60.0` | Request timeout in seconds |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate |


### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: claude-llm
    config:
      model: claude-3-opus-20240229
      temperature: 0.7
      max_tokens: 4096
```

### Features

- **Tool Use**: Native support for Anthropic tool use with input_schema format
- **Vision**: Image analysis capabilities
- **Streaming**: Real-time response streaming
- **System Messages**: Dedicated system message handling (extracted separately from message flow and passed as `system` parameter)

### Implementation Details

#### System Message Handling

Unlike other providers, Anthropic handles system messages separately:

- System messages are extracted from the conversation flow in [`_prepare_messages`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/anthropic.py:55)
- Multiple system messages are combined with spaces
- The combined system message is passed as the `system` parameter to the API

#### Tool Use Format

Anthropic uses a different tool format than OpenAI:

- Tools are defined with `input_schema` instead of `parameters`
- Tool calls use `tool_use` type with `input` field for arguments
- Tool results use `tool_result` type with `tool_use_id` reference

## GoogleLLM

Google Gemini model integration with Vertex AI support.

**Source**: [`src/xaibo/primitives/modules/llm/google.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/google.py)

**Module Path**: `xaibo.primitives.modules.llm.GoogleLLM`

**Dependencies**: `google` dependency group

**Protocols**: Provides [`LLMProtocol`](../protocols/llm.md)

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"gemini-2.0-flash-001"` | Google model name |
| `api_key` | `str` | `None` | Google API key (required for AI Studio mode, does not check environment variables) |
| `vertexai` | `bool` | `False` | Use Vertex AI instead of AI Studio (when true, uses service account authentication) |
| `project` | `str` | `None` | GCP project ID (required for Vertex AI mode) |
| `location` | `str` | `"us-central1"` | Vertex AI location |
| `temperature` | `float` | `None` | Default sampling temperature |
| `max_tokens` | `int` | `None` | Default maximum tokens to generate (mapped to `max_output_tokens` internally) |

**Note**: The `config` parameter is required for initialization. Either `api_key` (for AI Studio) or `vertexai=true` with `project` (for Vertex AI) must be provided.


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
- **Function Calling**: Google function calling with parameter mapping to FunctionDeclaration format
- **Image Format Detection**: Automatic MIME type detection for images based on file extensions (supports .png, .gif, .webp, defaults to .jpeg)
- **Streaming**: Real-time response streaming
- **Safety Settings**: Configurable content safety filters

### Implementation Details

#### Image Format Detection

The [`_convert_image`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/llm/google.py:102) method handles both data URIs and file URLs:

- **Data URIs**: Extracts MIME type and base64 data automatically
- **File URLs**: Detects format from extension (.png, .gif, .webp) or defaults to image/jpeg
- **Vertex AI vs AI Studio**: Automatically configures client based on `vertexai` parameter

#### System Message Handling

System messages are extracted from the message flow and passed as the `system_instruction` parameter to the Google API, separate from the conversation contents.

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


### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.BedrockLLM
    id: bedrock-llm
    config:
      model: anthropic.claude-v2
      region_name: us-west-2
      temperature: 0.7
      max_tokens: 4096
```

### Features

- **Multi-Provider**: Access to multiple model providers through Bedrock Converse API
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
| `llms` | `List[LLMProtocol]` | List of LLM instances to combine (passed as constructor parameter) |

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
      model: claude-3-opus-20240229
  
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
| `responses` | `List[Dict]` | `[]` | Predefined responses in LLMResponse format |
| `streaming_delay` | `int` | `0` | Delay between streaming chunks (ms) |
| `streaming_chunk_size` | `int` | `3` | Characters per streaming chunk |

### Example Configuration

```yaml
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: mock-llm
    config:
      responses:
        - content: "This is the first mock response."
        - content: "This is the second mock response."
        - content: "This is the third mock response."
      streaming_delay: 50
      streaming_chunk_size: 5
```

### Features

- **Deterministic**: Predictable responses for testing
- **Cycling**: Cycles through responses list
- **Streaming Simulation**: Simulates streaming with configurable delays
- **No Dependencies**: No external API dependencies


## Error Handling

All LLM modules handle common error scenarios:

### Authentication Errors

```python
# Missing API key
ValueError: "API key not provided and OPENAI_API_KEY not set"

# Invalid API key
Exception: "Invalid API key provided"
```

### Rate Limiting

```python
# Rate limit exceeded
Exception: "Rate limit exceeded. Retry after 60 seconds"
```

### Model Errors

```python
# Model not found
Exception: "Model 'invalid-model' not found"

# Context length exceeded
Exception: "Request exceeds maximum context length of 4096 tokens"
```

### Network Errors

```python
# Timeout
Exception: "Request timed out after 60 seconds"

# Connection error
Exception: "Failed to connect to API endpoint"
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