# LiveKit Voice Assistant Example

This example demonstrates how to create a voice assistant using Xaibo agents with LiveKit's real-time communication platform.

## What it does

The [`agent.py`](agent.py) file creates a LiveKit voice assistant that:

- Loads Xaibo agents from YAML configuration files in the `./agents` directory
- Uses a Xaibo agent as the LLM backend for the voice assistant
- Integrates with OpenAI for speech-to-text and text-to-speech
- Uses Silero for voice activity detection
- Connects to LiveKit rooms for real-time voice conversations

## Configuration

### Environment Setup

Copy the [`.env`](.env) file and replace the placeholder values with your actual credentials:

```bash
# OpenAI Configuration (required for STT/TTS)
OPENAI_API_KEY=your_openai_api_key_here

# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_token_here
LIVEKIT_API_SECRET=your_livekit_api_secret_here
LIVEKIT_URL=your_livekit_url_here
```

### Getting LiveKit Credentials

1. Sign up for a [LiveKit Cloud](https://cloud.livekit.io/) account
2. Create a new project
3. Go to your project's **Settings** → **Keys** section
4. Copy the following values:
   - **API Key** → `LIVEKIT_API_KEY`
   - **Secret Key** → `LIVEKIT_API_SECRET`
   - **WebSocket URL** → `LIVEKIT_URL` (usually `wss://your-project.livekit.cloud`)

### Getting OpenAI API Key

1. Visit [OpenAI's API platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key to `OPENAI_API_KEY`

## Running the Agent

### Install Dependencies

```bash
uv sync
```

### Download Silero Models

Download the required Silero voice activity detection models:

```bash
uv run python agent.py download_dependencies
```

### Start the Agent

```bash
uv run python agent.py dev
```

The agent will connect to your LiveKit project and be ready to join voice conversations in LiveKit rooms.

## Testing with LiveKit Sandbox

For quick testing, you can use LiveKit's sandbox environment:

1. Visit [LiveKit Agents Playground](https://agents-playground.livekit.io/)
2. Enter your LiveKit URL and API credentials
3. Create or join a room
4. Your voice assistant will automatically join and respond to voice input

The sandbox provides a web interface to test voice conversations without building a custom client application.

## Debugging

For debugging your Xaibo agents during development, run the Xaibo development server in parallel:

### Terminal 1: Start Xaibo Dev Server
```bash
uv run xaibo dev
```

### Terminal 2: Start LiveKit Agent
```bash
uv run python agent.py dev
```

The Xaibo dev server provides a web interface to inspect agent configurations and monitor agent behavior while the LiveKit agent handles voice conversations.