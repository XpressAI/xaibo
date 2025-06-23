# How to Use Xaibo Agents in LiveKit Voice Assistants

This guide shows you how to integrate your Xaibo agents with LiveKit's voice assistant framework to create real-time conversational AI applications.

*See also: [LiveKit Integration Reference](../../reference/integrations/livekit.md)*

!!! example "Complete Working Example"
    For a ready-to-run implementation, see the [LiveKit Example](https://github.com/xpressai/xaibo/tree/main/examples/livekit_example) which includes:
    
    - Complete [`agent.py`](https://github.com/xpressai/xaibo/blob/main/examples/livekit_example/agent.py) implementation
    - Environment configuration template ([`.env`](https://github.com/xpressai/xaibo/blob/main/examples/livekit_example/.env))
    - Project dependencies ([`pyproject.toml`](https://github.com/xpressai/xaibo/blob/main/examples/livekit_example/pyproject.toml))
    - Detailed setup and usage instructions ([`README.md`](https://github.com/xpressai/xaibo/blob/main/examples/livekit_example/README.md))


## Prerequisites

- Python 3.10 or higher
- uv package manager installed
- Agent configurations in YAML format
- Environment variables configured (`.env` file)

## Install Dependencies

Install Xaibo with LiveKit integration support:

```bash
uv add xaibo[livekit]
```

Install LiveKit agents framework and speech plugins:

```bash
uv add livekit-agents livekit-plugins-openai livekit-plugins-silero
```

## Set Up Your LiveKit Worker

Create a new Python file for your LiveKit worker (e.g., `voice_assistant.py`):

```python
import logging
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    Agent,
    AgentSession
)
from livekit.plugins import openai, silero

from xaibo.integrations.livekit import XaiboAgentLoader

# Load environment variables
load_dotenv(dotenv_path=".env")

# Configure logging
logger = logging.getLogger("xaibo-voice-assistant")
logger.setLevel(logging.INFO)
```

## Load Your Xaibo Agents

Use the [`XaiboAgentLoader`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py) to load your agent configurations:

```python
# Initialize the agent loader
loader = XaiboAgentLoader()

# Load all agents from your configuration directory
loader.load_agents_from_directory("./agents")

# Enable debug logging (optional)
loader.enable_debug_logging("./debug")
```

## Create Your Voice Assistant

Get an LLM instance from your loaded agent and configure the LiveKit assistant:

```python
# Get the LLM for your specific agent
llm = loader.get_llm("your-agent-id")

# Create the voice assistant with speech components
assistant = Agent(
    instructions="",  # Instructions handled by Xaibo agent
    vad=silero.VAD.load(),  # Voice Activity Detection
    stt=openai.STT(),       # Speech-to-Text
    llm=llm,                # Your Xaibo agent as LLM
    tts=openai.TTS(),       # Text-to-Speech
)
```

## Implement the LiveKit Entrypoint

Create the main entrypoint function that LiveKit will call:

```python
async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room {ctx.room.name}")
    
    # Connect to the LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Start the agent session
    session = AgentSession()
    await session.start(
        agent=assistant,
        room=ctx.room,
    )
    
    logger.info("Voice assistant started")
```

## Run Your Voice Assistant

Add the main block to run your LiveKit worker:

```python
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
```

## Complete Example

Here's the complete working example:

```python
import logging
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    Agent,
    AgentSession
)
from livekit.plugins import openai, silero

from xaibo.integrations.livekit import XaiboAgentLoader

# Load environment variables
load_dotenv(dotenv_path=".env")

# Configure logging
logger = logging.getLogger("xaibo-voice-assistant")
logger.setLevel(logging.INFO)

# Load Xaibo agents
loader = XaiboAgentLoader()
loader.load_agents_from_directory("./agents")
loader.enable_debug_logging("./debug")

# Get LLM from your agent
llm = loader.get_llm("example")

# Create voice assistant
assistant = Agent(
    instructions="",
    vad=silero.VAD.load(),
    stt=openai.STT(),
    llm=llm,
    tts=openai.TTS(),
)

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession()
    await session.start(
        agent=assistant,
        room=ctx.room,
    )
    
    logger.info("Voice assistant started")

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
```

## Run Your Voice Assistant

Execute your voice assistant worker:

```bash
python voice_assistant.py dev
```

## Advanced Configuration

### Enable File Watching

Automatically reload agent configurations when files change:

```python
loader.enable_file_watching("./agents")
```

### List Available Agents

Check which agents are loaded:

```python
available_agents = loader.list_agents()
print(f"Available agents: {available_agents}")
```

### Get Agent Information

Retrieve detailed information about a specific agent:

```python
agent_info = loader.get_agent_info("your-agent-id")
print(f"Agent modules: {agent_info['modules']}")
```

### Custom Debug Directory

Specify a custom directory for debug traces:

```python
loader.enable_debug_logging("./custom-debug-path")
```

## Environment Variables

Ensure your `.env` file contains the necessary API keys:

```env
OPENAI_API_KEY=your_openai_api_key
LIVEKIT_URL=your_livekit_server_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

## Troubleshooting

### Agent Not Found Error

If you get an "Agent not found" error:

1. Verify your agent YAML files are in the correct directory
2. Check that the agent ID matches what's in your YAML configuration
3. Use [`loader.list_agents()`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/integrations/livekit/agent_loader.py:97) to see available agents

### Debug Logging Issues

If debug logging fails to enable:

1. Ensure you have the UI dependencies installed
2. Check that the debug directory is writable
3. Verify the debug directory path exists or can be created

### Connection Issues

For LiveKit connection problems:

1. Verify your LiveKit server URL and credentials
2. Check network connectivity to your LiveKit server
3. Ensure your room name is valid and accessible