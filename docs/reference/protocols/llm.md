# LLM Protocol Specification

The LLM Protocol defines the interface for language model integration in Xaibo agents. It provides standardized methods for text generation and streaming responses.

**Source**: [`src/xaibo/core/protocols/llm.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/llm.py)

## LLMProtocol

The core protocol interface for language model implementations.

```python
@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol for interacting with LLM models"""
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        ...
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM"""
        yield ...
```

### Methods

---

#### `generate(messages, options=None) -> LLMResponse`

Generate a complete response from the language model.

**Parameters:**

- `messages` (`List[LLMMessage]`, required): Conversation history and current input
- `options` (`Optional[LLMOptions]`, optional): Generation parameters and tool definitions

**Returns:**

- `LLMResponse`: Complete response with content, tool calls, and usage statistics

**Example:**
```python
messages = [
    LLMMessage.system("You are a helpful assistant"),
    LLMMessage.user("What is the capital of France?")
]

options = LLMOptions(
    temperature=0.7,
    max_tokens=100
)

response = await llm.generate(messages, options)
print(response.content)  # "The capital of France is Paris."
```

---

#### `generate_stream(messages, options=None) -> AsyncIterator[str]`

Generate a streaming response from the language model.

**Parameters:**

- `messages` (`List[LLMMessage]`, required): Conversation history and current input
- `options` (`Optional[LLMOptions]`, optional): Generation parameters and tool definitions

**Returns:**

- `AsyncIterator[str]`: Stream of text chunks as they are generated

**Example:**
```python
async for chunk in llm.generate_stream(messages, options):
    print(chunk, end="", flush=True)
```
---

## Data Models

### LLMMessage

Represents a message in the conversation history.

**Source**: [`src/xaibo/core/models/llm.py:40`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L40)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | `LLMRole` | Yes | Message role (system, user, assistant, function) |
| `content` | `List[LLMMessageContent]` | Yes | Message content (text, images, etc.) |
| `name` | `str` | No | Optional name for the message sender |
| `tool_calls` | `List[LLMFunctionCall]` | No | Function calls made by the assistant |
| `tool_results` | `List[LLMFunctionResult]` | No | Results from function executions |

#### Class Methods

---

##### `system(content: str, name: Optional[str] = None) -> LLMMessage`

Create a system message.

```python
msg = LLMMessage.system("You are a helpful assistant")
```

---

##### `user(content: str, name: Optional[str] = None) -> LLMMessage`

Create a user message.

```python
msg = LLMMessage.user("Hello, how are you?")
```

---

##### `user_image(image_path: str, name: Optional[str] = None) -> LLMMessage`

Create a user message with an image.

```python
msg = LLMMessage.user_image("/path/to/image.jpg")
```

---

##### `assistant(content: str, name: Optional[str] = None) -> LLMMessage`

Create an assistant message.

```python
msg = LLMMessage.assistant("I'm doing well, thank you!")
```

---

##### `function(id: str, name: str, arguments: Dict[str, Any]) -> LLMMessage`

Create a function call message.

```python
msg = LLMMessage.function("call_123", "get_weather", {"city": "Paris"})
```

---

##### `function_result(id: str, name: str, content: str) -> LLMMessage`

Create a function result message.

```python
msg = LLMMessage.function_result("call_123", "get_weather", "Sunny, 22°C")
```

---

### LLMRole

Enumeration of message roles.

**Source**: [`src/xaibo/core/models/llm.py:10`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L10)

| Value | Description |
|-------|-------------|
| `SYSTEM` | System instructions and context |
| `USER` | User input messages |
| `ASSISTANT` | Assistant responses |
| `FUNCTION` | Function calls and results |

### LLMMessageContent

Content within a message supporting multiple modalities.

**Source**: [`src/xaibo/core/models/llm.py:34`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L34)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `LLMMessageContentType` | Yes | Content type (text or image) |
| `text` | `str` | No | Text content (required if type is TEXT) |
| `image` | `str` | No | Base64-encoded image data URI (required if type is IMAGE) |

### LLMMessageContentType

Enumeration of content types.

**Source**: [`src/xaibo/core/models/llm.py:17`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L17)

| Value | Description |
|-------|-------------|
| `TEXT` | Plain text content |
| `IMAGE` | Image content (base64 data URI) |

### LLMOptions

Configuration options for LLM generation.

**Source**: [`src/xaibo/core/models/llm.py:90`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L90)

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `temperature` | `float` | `1.0` | Sampling temperature (0.0-2.0) |
| `top_p` | `float` | `1.0` | Nucleus sampling parameter (0.0-1.0) |
| `max_tokens` | `int` | `None` | Maximum tokens to generate |
| `stop_sequences` | `List[str]` | `None` | Sequences that stop generation |
| `functions` | `List[Tool]` | `None` | Available tools for function calling |
| `vendor_specific` | `Dict[str, Any]` | `{}` | Provider-specific options |

#### Validation

- `temperature`: Must be between 0.0 and 2.0
- `top_p`: Must be between 0.0 and 1.0

### LLMResponse

Response from language model generation.

**Source**: [`src/xaibo/core/models/llm.py:121`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L121)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | `str` | Yes | Generated text content |
| `tool_calls` | `List[LLMFunctionCall]` | No | Function calls requested by the model |
| `usage` | `LLMUsage` | No | Token usage statistics |
| `vendor_specific` | `Dict[str, Any]` | No | Provider-specific response data |

#### Class Methods

---

##### `merge(*responses: LLMResponse) -> LLMResponse`

Merge multiple responses into a single response.

```python
response1 = LLMResponse(content="Hello")
response2 = LLMResponse(content="World")
merged = LLMResponse.merge(response1, response2)
print(merged.content)  # "Hello\nWorld"
```

---

### LLMFunctionCall

Function call information from the model.

**Source**: [`src/xaibo/core/models/llm.py:22`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L22)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier for the function call |
| `name` | `str` | Yes | Name of the function to call |
| `arguments` | `Dict[str, Any]` | Yes | Function arguments as key-value pairs |

### LLMFunctionResult

Result from executing a function call.

**Source**: [`src/xaibo/core/models/llm.py:28`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L28)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Identifier matching the original function call |
| `name` | `str` | Yes | Name of the executed function |
| `content` | `str` | Yes | String representation of the function result |

### LLMUsage

Token usage statistics from the model.

**Source**: [`src/xaibo/core/models/llm.py:114`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/llm.py#L114)

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt_tokens` | `int` | Yes | Tokens used in the input prompt |
| `completion_tokens` | `int` | Yes | Tokens generated in the response |
| `total_tokens` | `int` | Yes | Total tokens used (prompt + completion) |

## Implementation Example

```python
from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMResponse, LLMUsage

class CustomLLM:
    """Example LLM implementation"""
    
    def __init__(self, config: dict):
        self.model = config.get("model", "default-model")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.example.com")
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> LLMResponse:
        # Convert messages to API format
        api_messages = self._convert_messages(messages)
        
        # Prepare request parameters
        params = {
            "model": self.model,
            "messages": api_messages
        }
        
        if options:
            if options.temperature is not None:
                params["temperature"] = options.temperature
            if options.max_tokens is not None:
                params["max_tokens"] = options.max_tokens
            if options.functions:
                params["tools"] = self._convert_tools(options.functions)
        
        # Make API request
        response = await self._api_request(params)
        
        # Convert response
        return LLMResponse(
            content=response["choices"][0]["message"]["content"],
            usage=LLMUsage(
                prompt_tokens=response["usage"]["prompt_tokens"],
                completion_tokens=response["usage"]["completion_tokens"],
                total_tokens=response["usage"]["total_tokens"]
            )
        )
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage], 
        options: Optional[LLMOptions] = None
    ) -> AsyncIterator[str]:
        # Similar to generate but with streaming
        params = self._prepare_params(messages, options)
        params["stream"] = True
        
        async for chunk in self._api_stream(params):
            if chunk.get("choices") and chunk["choices"][0].get("delta"):
                content = chunk["choices"][0]["delta"].get("content", "")
                if content:
                    yield content
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List[dict]:
        """Convert LLMMessage objects to API format"""
        api_messages = []
        for msg in messages:
            api_msg = {"role": msg.role.value}
            
            if msg.content:
                if len(msg.content) == 1 and msg.content[0].type == "text":
                    api_msg["content"] = msg.content[0].text
                else:
                    api_msg["content"] = [
                        self._convert_content(content) for content in msg.content
                    ]
            
            if msg.tool_calls:
                api_msg["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments)
                        }
                    }
                    for call in msg.tool_calls
                ]
            
            api_messages.append(api_msg)
        
        return api_messages
```

## Error Handling

Implementations should handle and propagate appropriate exceptions:

```python
class LLMError(Exception):
    """Base exception for LLM errors"""
    pass

class LLMRateLimitError(LLMError):
    """Rate limit exceeded"""
    pass

class LLMAuthenticationError(LLMError):
    """Authentication failed"""
    pass

class LLMModelNotFoundError(LLMError):
    """Requested model not available"""
    pass
```

## Testing

Mock implementation for testing:

```python
class MockLLM:
    def __init__(self, responses: List[str]):
        self.responses = responses
        self.call_count = 0
    
    async def generate(self, messages, options=None):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return LLMResponse(
            content=response,
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        )
    
    async def generate_stream(self, messages, options=None):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        for word in response.split():
            yield word + " "

# Verify protocol compliance
assert isinstance(MockLLM([]), LLMProtocol)
```