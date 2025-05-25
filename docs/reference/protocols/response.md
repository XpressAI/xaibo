# Response Protocol Specification

The Response Protocol defines the interface for sending responses from Xaibo agents. It provides standardized methods for delivering text, multimedia content, and complex responses with attachments.

**Source**: [`src/xaibo/core/protocols/response.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/protocols/response.py)

## ResponseProtocol

The core protocol interface for response handling implementations.

```python
@runtime_checkable
class ResponseProtocol(Protocol):
    """Protocol for sending responses"""
    
    async def get_response(self) -> Response:
        """Get the current response object"""
        ...
    
    async def respond_text(self, response: str) -> None:
        """Send a response"""
        ...
    
    async def respond_image(self, iolike: BinaryIO) -> None:
        """Send an image response"""
        ...
    
    async def respond_audio(self, iolike: BinaryIO) -> None:
        """Send an audio response"""
        ...
    
    async def respond_file(self, iolike: BinaryIO) -> None:
        """Send a file response"""
        ...
    
    async def respond(self, response: Response) -> None:
        """Send a complex response containing text and/or file attachments"""
        ...
```

### Methods

---

#### `get_response() -> Response`

Retrieve the current response object containing accumulated text and attachments.

**Returns:**

- [`Response`](#response): The current response object with text content and file attachments

**Example:**
```python
current_response = await response_handler.get_response()
if current_response.text:
    print(f"Response text: {current_response.text}")
if current_response.attachments:
    print(f"Attachments: {len(current_response.attachments)}")
```

---

#### `respond_text(response) -> None`

Send a text response to the user.

**Parameters:**

- `response` (`str`, required): The response text to send

**Example:**
```python
await response_handler.respond_text("Hello! How can I help you today?")
```

---

#### `respond_image(iolike) -> None`

Send an image response to the user.

**Parameters:**

- `iolike` (`BinaryIO`, required): IO object containing the image data

**Example:**
```python
with open("chart.png", "rb") as image_file:
    await response_handler.respond_image(image_file)
```

---

#### `respond_audio(iolike) -> None`

Send an audio response to the user.

**Parameters:**

- `iolike` (`BinaryIO`, required): IO object containing the audio data

**Example:**
```python
with open("speech.mp3", "rb") as audio_file:
    await response_handler.respond_audio(audio_file)
```

---

#### `respond_file(iolike) -> None`

Send a file response to the user.

**Parameters:**
- `iolike` (`BinaryIO`, required): IO object containing the file data

**Example:**
```python
with open("report.pdf", "rb") as file:
    await response_handler.respond_file(file)
```

---

#### `respond(response) -> None`

Send a complex response containing text and/or file attachments.

**Parameters:**
- `response` ([`Response`](#response), required): Response object containing text and attachments

**Example:**
```python
attachments = [
    FileAttachment(image_data, FileType.IMAGE),
    FileAttachment(audio_data, FileType.AUDIO)
]
complex_response = Response(
    text="Here's your analysis with supporting materials:",
    attachments=attachments
)
await response_handler.respond(complex_response)
```

---

## Data Structures

### Response

Model for responses that can include text and file attachments.

**Source**: [`src/xaibo/core/models/response.py`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/models/response.py)

```python
class Response:
    """Model for responses that can include text and file attachments"""
    text: Optional[str] = None
    attachments: List[FileAttachment] = []
    
    def __init__(
        self, 
        text: Optional[str] = None, 
        attachments: Optional[List[FileAttachment]] = None
    ) -> None:
        ...
```

**Attributes:**

- `text` (`Optional[str]`): Text content of the response
- `attachments` (`List[FileAttachment]`): List of file attachments

### FileAttachment

Model for file attachments in responses.

```python
class FileAttachment:
    """Model for file attachments in responses"""
    content: BinaryIO
    type: FileType
    
    def __init__(self, content: BinaryIO, type: FileType) -> None:
        ...
```

**Attributes:**

- `content` (`BinaryIO`): IO object containing the file data
- `type` ([`FileType`](#filetype)): Type classification of the file

### FileType

Enumeration for different types of file attachments.

```python
class FileType(Enum):
    """Enum for different types of file attachments"""
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"
```

**Values:**

- `IMAGE`: Image file attachments (PNG, JPEG, GIF, etc.)
- `AUDIO`: Audio file attachments (MP3, WAV, etc.)
- `FILE`: Generic file attachments (PDF, documents, etc.)

## Implementation Requirements

### Asynchronous Operations

All protocol methods must be implemented as asynchronous functions using `async`/`await` syntax.

### Error Handling

Implementations must handle the following error conditions:

- **Invalid file data**: When `BinaryIO` objects contain invalid or corrupted data
- **Unsupported file types**: When file types are not supported by the response handler
- **Network failures**: When response delivery fails due to connectivity issues
- **Resource limits**: When file sizes exceed implementation-specific limits

### Thread Safety

Response protocol implementations must be thread-safe when accessed from multiple concurrent tasks.

## Usage Patterns in Orchestrator Modules

### Basic Text Response

```python
class SimpleOrchestrator:
    def __init__(self, response: ResponseProtocol):
        self.response = response
    
    async def handle_message(self, message: str):
        result = await self.process_message(message)
        await self.response.respond_text(result)
```

### Multi-Modal Response

```python
class AnalysisOrchestrator:
    def __init__(self, response: ResponseProtocol):
        self.response = response
    
    async def generate_report(self, data):
        # Generate text analysis
        analysis_text = await self.analyze_data(data)
        
        # Generate visualization
        chart_data = await self.create_chart(data)
        
        # Send combined response
        attachments = [FileAttachment(chart_data, FileType.IMAGE)]
        response = Response(text=analysis_text, attachments=attachments)
        await self.response.respond(response)
```

### Streaming Response Pattern

```python
class StreamingOrchestrator:
    def __init__(self, response: ResponseProtocol):
        self.response = response
    
    async def process_long_task(self, request):
        # Send initial response
        await self.response.respond_text("Processing your request...")
        
        # Process and send intermediate results
        for step_result in self.process_steps(request):
            await self.response.respond_text(f"Step completed: {step_result}")
        
        # Send final response with attachments
        final_result = await self.finalize_processing()
        await self.response.respond(final_result)
```

## Error Handling Specifications

### Exception Types

Implementations should raise appropriate exceptions for error conditions:

- `ValueError`: For invalid response content or malformed data
- `IOError`: For file I/O related errors
- `ConnectionError`: For network-related response delivery failures
- `RuntimeError`: For general response handling failures

### Error Recovery

Response handlers should implement graceful error recovery:

1. **Retry Logic**: Automatic retry for transient network failures
2. **Fallback Responses**: Alternative response methods when primary method fails
3. **Error Logging**: Comprehensive logging of error conditions for debugging
4. **Partial Delivery**: Ability to deliver partial responses when complete delivery fails

### Timeout Handling

Response operations must implement appropriate timeouts:

- **Text responses**: 30 seconds maximum
- **File uploads**: 5 minutes maximum for large files
- **Network operations**: Configurable timeout with reasonable defaults