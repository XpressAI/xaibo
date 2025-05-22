# Google Calendar Example for Xaibo

A simple example showing how to integrate Google Calendar with a Xaibo agent.

## Setup

### 1. Install Dependencies

```bash
cd examples/google_calendar_example
pip install -e .
```

### 2. Set Up Google Calendar API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Download the JSON file and save it as `credentials.json` in this directory

### 3. Run the Agent

```bash
# Start the Xaibo development server
uv run xaibo dev
```

The agent will be available at `http://127.0.0.1:9001`

## Usage

### Authentication

On first use, the agent will automatically open a browser window for Google OAuth authentication. After granting permission, a `token.pickle` file will be created for future use.

### Example Prompts

Try these prompts with your agent:

```
What events do I have coming up this week?
```

```
Create a meeting called "Team Standup" tomorrow at 10 AM for 30 minutes.
```

```
Show me my calendar information.
```

```
List my events for the next 3 days.
```

## Available Tools

The agent has access to these Google Calendar tools:

- **`list_events()`** - List upcoming events from your primary calendar
- **`create_event()`** - Create a new calendar event
- **`get_calendar_info()`** - Get information about your primary calendar

## File Structure

```
├── agents/
│   └── example.yml          # Agent configuration
├── tools/
│   └── calendar_tools.py    # Google Calendar tools
├── tests/
│   └── test_example.py      # Basic tests
├── pyproject.toml           # Dependencies
└── README.md               # This file
```

## API Usage

You can also interact with the agent via the OpenAI-compatible API:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What meetings do I have today?"}
    ]
  }'
```

## Troubleshooting

**Authentication Issues:**
- Make sure `credentials.json` is in the project directory
- Delete `token.pickle` and re-authenticate if you get permission errors

**API Errors:**
- Verify the Google Calendar API is enabled in your Google Cloud project
- Check that your OAuth consent screen is properly configured

**Import Errors:**
- Make sure you've installed the dependencies with `pip install -e .`