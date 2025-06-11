# LiveKit Integration Reference

*See also: [How to Use Xaibo Agents in LiveKit Voice Assistants](../../how-to/integrations/livekit-voice-assistant.md)*

The Xaibo LiveKit integration provides classes and utilities for using Xaibo agents within LiveKit's voice assistant framework.

## Module: `xaibo.integrations.livekit`

### Classes

#### [`XaiboAgentLoader`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:14)

LiveKit-Xaibo integration helper that enables direct use of Xaibo agents in LiveKit applications with YAML loading and debugging.

**Constructor:**
```python
XaiboAgentLoader() -> None
```

Initializes the XaiboAgentLoader with a new Xaibo instance.

**Methods:**

##### [`load_agents_from_directory(directory: str) -> None`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:33)

Load all agent configurations from a directory.

Recursively scans the specified directory for YAML files containing agent configurations and registers them with the Xaibo instance.

**Parameters:**
- `directory` (str): Path to directory containing YAML agent configurations

**Raises:**
- `ValueError`: If any YAML files cannot be parsed as valid agent configs
- `FileNotFoundError`: If the directory does not exist

##### [`get_llm(agent_id: str) -> XaiboLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:75)

Get a configured XaiboLLM instance for the specified agent.

**Parameters:**
- `agent_id` (str): The ID of the agent to get an LLM instance for

**Returns:**
- [`XaiboLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:26): A configured LLM instance ready for use with LiveKit

**Raises:**
- `ValueError`: If the agent ID is not found in loaded configurations

##### [`list_agents() -> List[str]`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:97)

List all available agent IDs.

**Returns:**
- `List[str]`: List of agent IDs that have been loaded

##### [`get_agent_info(agent_id: str) -> Dict[str, Any]`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:106)

Get agent metadata and configuration details.

**Parameters:**
- `agent_id` (str): The ID of the agent to get information for

**Returns:**
- `Dict[str, Any]`: Dictionary containing agent metadata including id, description, modules, and exchange configuration

**Raises:**
- `ValueError`: If the agent ID is not found

##### [`enable_debug_logging(debug_dir: str = "./debug") -> None`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:152)

Enable Xaibo's debug logging system.

Enables the same debugging capabilities as the Xaibo web server, writing debug traces to the specified directory.

**Parameters:**
- `debug_dir` (str, optional): Directory to write debug traces to. Defaults to "./debug"

**Raises:**
- `ValueError`: If debug logging dependencies are not available

##### [`enable_file_watching(directory: str) -> None`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:184)

Enable automatic reloading of agent configurations when files change.

Starts a background task that watches the specified directory for changes and automatically reloads agent configurations when YAML files are modified, added, or removed.

**Parameters:**
- `directory` (str): Directory to watch for configuration changes

**Raises:**
- `RuntimeError`: If file watching is already enabled for a different directory

##### [`disable_file_watching() -> None`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:211)

Disable automatic file watching if it's currently enabled.

##### [`get_xaibo_instance() -> Xaibo`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:241)

Get the underlying Xaibo instance.

Provides access to the raw Xaibo instance for advanced use cases that require direct interaction with the Xaibo framework.

**Returns:**
- [`Xaibo`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/xaibo.py): The underlying Xaibo instance

##### [`is_debug_enabled() -> bool`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:253)

Check if debug logging is currently enabled.

**Returns:**
- `bool`: True if debug logging is enabled, False otherwise

##### [`get_debug_directory() -> Optional[str]`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:262)

Get the current debug directory if debug logging is enabled.

**Returns:**
- `Optional[str]`: The debug directory path, or None if debug logging is disabled

#### [`XaiboLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:26)

Xaibo LLM implementation that integrates with Xaibo's agent system.

Bridges LiveKit's LLM interface with Xaibo's agent-based conversational AI system, allowing Xaibo agents to be used as LLM providers in LiveKit applications.

**Constructor:**
```python
XaiboLLM(*, xaibo: Xaibo, agent_id: str) -> None
```

Initialize the Xaibo LLM.

**Parameters:**
- `xaibo` ([`Xaibo`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/xaibo.py)): The Xaibo instance to use for agent management
- `agent_id` (str): The ID of the Xaibo agent to use for processing

**Methods:**

##### [`chat(...) -> XaiboLLMStream`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:57)

Create a chat stream for the given context.

```python
chat(
    *,
    chat_ctx: ChatContext,
    tools: list[FunctionTool | RawFunctionTool] | None = None,
    conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
    tool_choice: NotGivenOr[ToolChoice] = NOT_GIVEN,
    extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
) -> XaiboLLMStream
```

**Parameters:**
- `chat_ctx` (ChatContext): The chat context containing the conversation history
- `tools` (list[FunctionTool | RawFunctionTool] | None, optional): Function tools available for the agent (currently not used)
- `conn_options` (APIConnectOptions, optional): Connection options for the stream
- `parallel_tool_calls` (NotGivenOr[bool], optional): Whether to allow parallel tool calls (currently not used)
- `tool_choice` (NotGivenOr[ToolChoice], optional): Tool choice strategy (currently not used)
- `extra_kwargs` (NotGivenOr[dict[str, Any]], optional): Additional keyword arguments (currently not used)

**Returns:**
- [`XaiboLLMStream`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:170): A stream for processing the chat

#### [`XaiboLLMStream`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:170)

Xaibo LLM stream implementation that handles real-time streaming responses from Xaibo agents.

Provides true streaming output by using a queue-based system that streams chunks the moment they become available from the Xaibo agent. The implementation creates an agent with both conversation history and streaming response handler injected via ConfigOverrides, enabling real-time response streaming rather than simulated streaming.

**Constructor:**
```python
XaiboLLMStream(
    llm: XaiboLLM,
    *,
    chat_ctx: ChatContext,
    tools: list[FunctionTool | RawFunctionTool],
    conn_options: APIConnectOptions,
    xaibo: Xaibo,
    agent_id: str,
    conversation: SimpleConversation,
) -> None
```

Initialize the Xaibo LLM stream.

**Parameters:**
- `llm` ([`XaiboLLM`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:26)): The parent XaiboLLM instance
- `chat_ctx` (ChatContext): The chat context to process
- `tools` (list[FunctionTool | RawFunctionTool]): Available function tools
- `conn_options` (APIConnectOptions): Connection options
- `xaibo` ([`Xaibo`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/core/xaibo.py)): The Xaibo instance
- `agent_id` (str): The agent ID to use
- `conversation` ([`SimpleConversation`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/conversation/conversation.py)): The conversation history

**Methods:**

##### [`_create_streaming_response_handler(chunk_queue: Queue)`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:257)

Create a streaming response handler that puts chunks into a queue.

**Parameters:**
- `chunk_queue` (Queue): The queue to put streaming chunks into

**Returns:**
- StreamingResponse: A response handler that streams to the queue

##### [`_stream_chunks_from_queue(chunk_queue: Queue, agent_task) -> None`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:270)

Stream chunks from the queue as they become available.

**Parameters:**
- `chunk_queue` (Queue): The queue containing streaming text chunks
- `agent_task`: The background task running the agent

##### [`_send_final_usage_chunk(total_content: str) -> None`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/llm.py:310)

Send the final usage chunk with token information.

**Parameters:**
- `total_content` (str): The complete response content for token counting

### Functions

#### [`logger`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/log.py:3)

Logger instance for the LiveKit integration module.

```python
logger: logging.Logger
```

Logger configured with the name "xaibo.integrations.livekit" for integration-specific logging.

## Usage Examples

### Basic Agent Loading

```python
from xaibo.integrations.livekit import XaiboAgentLoader

loader = XaiboAgentLoader()
loader.load_agents_from_directory("./agents")
llm = loader.get_llm("my-agent")
```

### With Debug Logging

```python
loader = XaiboAgentLoader()
loader.load_agents_from_directory("./agents")
loader.enable_debug_logging("./debug")
```

### With File Watching

```python
loader = XaiboAgentLoader()
loader.load_agents_from_directory("./agents")
loader.enable_file_watching("./agents")
```

### LiveKit Integration

```python
from livekit.agents import Agent
from livekit.plugins import openai, silero

llm = loader.get_llm("my-agent")
assistant = Agent(
    instructions="",
    vad=silero.VAD.load(),
    stt=openai.STT(),
    llm=llm,
    tts=openai.TTS(),
)
```

## Installation

Install with LiveKit integration support:

```bash
uv add xaibo[livekit]
```

## Dependencies

The LiveKit integration requires:

- `livekit-agents`: Core LiveKit agents framework
- `watchfiles`: For file watching functionality
- Xaibo core modules and protocols

Optional dependencies for speech services:
- `livekit-plugins-openai`: OpenAI STT/TTS services
- `livekit-plugins-silero`: Silero VAD service