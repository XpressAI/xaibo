# Getting Started with Your First Xaibo Agent

In this lesson, you'll create your first Xaibo agent from scratch. You'll install the framework, set up a new project, and see your agent respond to messages. By the end, you'll have a working AI assistant running on your computer.

## Step 1: Install Xaibo

**Prerequisites:** Ensure you have Python 3.10 or higher installed on your system.

First, let's install the `uv` package manager if you don't have it:

```bash
pip install uv
```

You should see output similar to:
```
Installing collected packages: uv                                               
Successfully installed uv-0.7.8                                                
```

!!! tip
    There are other installation options for `uv`: [uv getting started documentation](https://docs.astral.sh/uv/getting-started/installation/)

## Step 2: Create Your First Project

Now create a new Xaibo project. This command sets up everything you need:

```bash
uvx xaibo init my_first_agent
```

You will be asked to select the functionality you want, and then you'll see Xaibo creating your project structure and installing dependencies.
Make sure you select both `webserver` and `openai`. 

```asciinema-player
{
  "file": "casts/init-xaibo.cast",
  "mkap_theme": "none",
  "rows": 12,
  "auto_play": true,
  "fit": "none"
}
```

Let's look at what was created:

```bash
cd my_first_agent
ls -la
```

You should see:
```
agents/          # Agent configuration files
tools/           # Custom tool implementations  
modules/         # Custom modules (empty for now)
tests/           # Test files
.env             # Environment variables
```

## Step 3: Examine Your Agent Configuration

Let's look at the example agent that was created:

```bash
cat agents/example.yml
```

You'll see a configuration like this:

```yaml
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4.1-nano
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.example]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful assistant with access to a variety of tools.
```

This configuration defines three **modules**:

- **LLM module**: Connects to OpenAI's GPT-4.1 nano for language understanding
- **Tool provider**: Makes Python functions available as tools
- **Orchestrator**: Manages the conversation and decides when to use tools

## Step 4: Look at Your First Tool

Let's examine the example tool:

```bash
cat tools/example.py
```

You'll see:

```python
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
```

This simple function becomes a tool your agent can use. The [`@tool`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/python_tool_provider.py) decorator tells Xaibo to make this function available to your agent.

## Step 5: Set Up Your API Key

Before running your agent, you need an OpenAI API key. Open the `.env` file:

```bash
cat .env
```

You'll see:
```
OPENAI_API_KEY=your_openai_api_key_here
```

Replace `your_openai_api_key_here` with your actual OpenAI API key. If you don't have one, get it from [OpenAI's website](https://platform.openai.com/api-keys).

Edit the file:
```bash
# Use your preferred editor
nano .env
# or
code .env
```

## Step 6: Start Your Agent

Now let's start the development server:

```bash
uv run xaibo dev
```

You should see output like:
```
INFO:     Started server process [283833]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9001 (Press CTRL+C to quit)
```

Your agent is now running! The server provides:

- A **debug UI** at http://127.0.0.1:9000 for visualizing agent operations
- An **OpenAI-compatible API** at http://127.0.0.1:9001/openai for sending messages

## Step 7: Test Your Agent

Open a new terminal window (keep the server running) and test your agent:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Hello! What time is it?"}
    ]
  }'
```

You should see a response like:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! I'll check the current time for you.\n\nThe current time is 2024-01-15 14:30:22 UTC."
      }
    }
  ]
}
```

**Congratulations!** Your agent successfully:

1. Received your message
2. Decided to use the `current_time` tool
3. Called the tool function
4. Returned the result in a natural response

## Step 8: Explore the Debug UI

Open your web browser and go to http://127.0.0.1:9000. You'll see an empty dashboard (as of v0.1.2), with a navigation on the right. 
Click on **example** and you'll see the Xaibo debug interface showing:

- **Sequence diagram**: Visual representation of how your agent processed the request
- **Module interactions**: How the LLM, tools, and orchestrator worked together
- **Timing information**: How long each operation took

<div style="display: flex; gap: 10px; margin: 20px 0;">
  <div style="flex: 1;">
    <img src="/images/sequence-diagram.png" alt="Xaibo Debug UI - Sequence Diagram Overview" width="100%">
    <p><em>Sequence Diagram Overview</em></p>
  </div>
  <div style="flex: 1;">
    <img src="/images/detail-view.png" alt="Xaibo Debug UI - Detail View" width="100%">
    <p><em>Detail View of Component Interactions</em></p>
  </div>
</div>

To get the detail view of any one event, simply click on that event either in the sequence diagram or in the list of events on the left.

The detail view shows you all the information that is being captured for that particular call: When it happend, what module was called 
and what module triggered it. The arguments and the results are available in a convenient JSON view, where you can switch between text, tree and table view, depending on what exactly you need to see.

This visualization helps you understand exactly what your agent is doing.

## Step 9: Try More Interactions

Test your agent with different messages:

```bash
# Ask a general question
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Can you help me with math? What is 25 * 4?"}
    ]
  }'
```

```bash
# Ask for the time again
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What time is it now?"}
    ]
  }'
```

Notice how your agent:

- Uses the tool when you ask for time
- Answers math questions directly using the LLM
- Provides natural, conversational responses

## What You've Learned

In this lesson, you've:

✅ **Installed Xaibo** and created your first project  
✅ **Understood agent configuration** with modules and their roles  
✅ **Seen how tools work** with the `@tool` decorator  
✅ **Run a live agent** that responds to messages  
✅ **Tested tool usage** and saw your agent make decisions  
✅ **Explored the debug UI** to understand agent behavior  

## Understanding What Happened

Your agent demonstrates Xaibo's key concepts:

- **Modules**: Independent components (LLM, tools, orchestrator) that work together
- **Protocols**: Standardized interfaces that let modules communicate
- **Tools**: Python functions that give your agent new capabilities
- **Configuration**: YAML files that define how modules connect

## Next Steps

Your agent currently has one simple tool. In the next lesson, [Building Tools](building-tools.md), you'll learn how to create more sophisticated tools that give your agent powerful new capabilities.

Ready to make your agent more capable? Let's continue with [Building Tools](building-tools.md)!