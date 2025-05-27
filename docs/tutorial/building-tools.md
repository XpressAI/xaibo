# Building Tools for Your Agent

In this lesson, you'll learn how to create custom tools that give your agent new capabilities. You'll build practical tools step by step and see how they integrate seamlessly with your agent. By the end, your agent will be able to check weather, access calendar information, and perform calculations.

## What You'll Build

You'll create three new tools:

- **Weather tool**: Get weather information for any city
- **Calendar tool**: Access calendar entries for specific dates  
- **Calculator tool**: Perform mathematical calculations

## Step 1: Understanding Tool Structure

Let's first understand how tools work by examining the existing tool:

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

Key elements of a tool:

- **Import the decorator**: [`@tool`](https://github.com/xpressai/xaibo/blob/main/src/xaibo/primitives/modules/tools/python_tool_provider.py) from the tool provider
- **Function definition**: Regular Python function
- **Docstring**: Describes what the tool does (the agent uses this)
- **Return value**: What the agent receives back

## Step 2: Create a Weather Tool

Let's add a weather tool to your existing file. Open `tools/example.py`:

```bash
# Use your preferred editor
nano tools/example.py
# or
code tools/example.py
```

Add this weather function at the end of the file:

```python
@tool
def get_weather(city: str, country: str = "US"):
    """Gets the current weather for a city
    
    :param city: The city name
    :param country: The country code (default: US)
    """
    # This is a simple mock implementation
    # In a real application, you'd call a weather API
    weather_data = {
        "New York": "Sunny, 22°C",
        "London": "Cloudy, 15°C", 
        "Tokyo": "Rainy, 18°C",
        "Berlin": "Partly cloudy, 16°C",
        "Sydney": "Sunny, 25°C"
    }
    
    weather = weather_data.get(city, f"Weather data not available for {city}")
    return f"Weather in {city}, {country}: {weather}"
```

Your complete file should now look like:

```python
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def get_weather(city: str, country: str = "US"):
    """Gets the current weather for a city
    
    :param city: The city name
    :param country: The country code (default: US)
    """
    weather_data = {
        "New York": "Sunny, 22°C",
        "London": "Cloudy, 15°C", 
        "Tokyo": "Rainy, 18°C",
        "Berlin": "Partly cloudy, 16°C",
        "Sydney": "Sunny, 25°C"
    }
    
    weather = weather_data.get(city, f"Weather data not available for {city}")
    return f"Weather in {city}, {country}: {weather}"
```

## Step 3: Test Your Weather Tool

Restart your development server to load the new tool:

```bash
# Stop the server with Ctrl+C, then restart
uv run xaibo dev
```

You should see:
```
INFO:     Started server process [283833]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9001 (Press CTRL+C to quit)
```

Test the weather tool:

```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What is the weather like in London?"}
    ]
  }'
```

You should see your agent use the weather tool:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant", 
        "content": "I'll check the weather in London for you.\n\nWeather in London, US: Cloudy, 15°C"
      }
    }
  ]
}
```

## Step 4: Add a Calendar Tool

Let's add a more complex tool that handles calendar data. Add this function to your `tools/example.py`:

```python
@tool
def get_calendar(date: str):
    """Returns calendar entries for a specific date
    
    :param date: Date in YYYY-MM-DD format
    """
    from datetime import datetime, timedelta
    
    # Calculate today and tomorrow for demo data
    today = datetime.today().strftime("%Y-%m-%d")
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Mock calendar data
    calendar_data = {
        today: [
            {
                'time': '09:00-10:00',
                'title': 'Daily Standup',
                'participants': ['Alice', 'Bob', 'Charlie'],
                'location': 'Conference Room A'
            },
            {
                'time': '14:00-15:30', 
                'title': 'Project Review',
                'participants': ['Manager', 'Team Lead'],
                'location': 'Online'
            }
        ],
        tomorrow: [
            {
                'time': '10:00-11:00',
                'title': 'Client Meeting',
                'participants': ['Client', 'Sales Rep'],
                'location': 'Client Office'
            }
        ]
    }
    
    entries = calendar_data.get(date, [])
    if not entries:
        return f"No calendar entries found for {date}"
    
    result = f"Calendar entries for {date}:\n"
    for entry in entries:
        result += f"• {entry['time']}: {entry['title']}\n"
        result += f"  Participants: {', '.join(entry['participants'])}\n"
        result += f"  Location: {entry['location']}\n\n"
    
    return result.strip()
```

## Step 5: Add a Calculator Tool

Finally, let's add a calculator tool that can handle mathematical expressions:

```python
@tool
def calculate(expression: str):
    """Performs mathematical calculations
    
    :param expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
    """
    try:
        # Safe evaluation of mathematical expressions
        # Only allow basic math operations
        allowed_chars = set('0123456789+-*/()., ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic mathematical operations are allowed"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"
```

## Step 6: Complete Tool File

Your complete `tools/example.py` should now look like:

```python
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def get_weather(city: str, country: str = "US"):
    """Gets the current weather for a city
    
    :param city: The city name
    :param country: The country code (default: US)
    """
    weather_data = {
        "New York": "Sunny, 22°C",
        "London": "Cloudy, 15°C", 
        "Tokyo": "Rainy, 18°C",
        "Berlin": "Partly cloudy, 16°C",
        "Sydney": "Sunny, 25°C"
    }
    
    weather = weather_data.get(city, f"Weather data not available for {city}")
    return f"Weather in {city}, {country}: {weather}"

@tool
def get_calendar(date: str):
    """Returns calendar entries for a specific date
    
    :param date: Date in YYYY-MM-DD format
    """
    from datetime import datetime, timedelta
    
    today = datetime.today().strftime("%Y-%m-%d")
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    calendar_data = {
        today: [
            {
                'time': '09:00-10:00',
                'title': 'Daily Standup',
                'participants': ['Alice', 'Bob', 'Charlie'],
                'location': 'Conference Room A'
            },
            {
                'time': '14:00-15:30', 
                'title': 'Project Review',
                'participants': ['Manager', 'Team Lead'],
                'location': 'Online'
            }
        ],
        tomorrow: [
            {
                'time': '10:00-11:00',
                'title': 'Client Meeting',
                'participants': ['Client', 'Sales Rep'],
                'location': 'Client Office'
            }
        ]
    }
    
    entries = calendar_data.get(date, [])
    if not entries:
        return f"No calendar entries found for {date}"
    
    result = f"Calendar entries for {date}:\n"
    for entry in entries:
        result += f"• {entry['time']}: {entry['title']}\n"
        result += f"  Participants: {', '.join(entry['participants'])}\n"
        result += f"  Location: {entry['location']}\n\n"
    
    return result.strip()

@tool
def calculate(expression: str):
    """Performs mathematical calculations
    
    :param expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
    """
    try:
        allowed_chars = set('0123456789+-*/()., ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic mathematical operations are allowed"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"
```

## Step 7: Test All Your Tools

Restart the server to load all tools:

```bash
uv run xaibo dev
```

You should see:
```
INFO:     Started server process [283833]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:9001 (Press CTRL+C to quit)
```

Now test each tool:

**Test the calendar tool:**
```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What do I have on my calendar today?"}
    ]
  }'
```

**Test the calculator:**
```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "Calculate 15 * 8 + 32"}
    ]
  }'
```

**Test multiple tools in one conversation:**
```bash
curl -X POST http://127.0.0.1:9001/openai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "example",
    "messages": [
      {"role": "user", "content": "What time is it, and what is the weather in Tokyo?"}
    ]
  }'
```

## Step 8: Observe Tool Selection

Visit the debug UI at http://127.0.0.1:9000 and send different requests. Notice how your agent:

- **Chooses the right tool** for each request
- **Uses multiple tools** when needed
- **Handles errors gracefully** (try asking for weather in a city not in the data)
- **Provides natural responses** combining tool results with conversational text

## Understanding Tool Parameters

Your tools demonstrate different parameter patterns:

**Simple tool (no parameters):**
```python
@tool
def current_time():
    # No parameters needed
```

**Required parameters:**
```python
@tool  
def get_weather(city: str, country: str = "US"):
    # city is required, country has a default
```

**Type hints help the agent:**

- `str` for text
- `int` for numbers  
- `bool` for true/false
- Default values make parameters optional

## Tool Best Practices

✅ **Clear docstrings**: Help the agent understand when to use the tool  
✅ **Type hints**: Guide the agent on what data to provide  
✅ **Error handling**: Return helpful messages when things go wrong  
✅ **Meaningful returns**: Provide data the agent can use in responses  
✅ **Simple functions**: Each tool does one thing well  

## What You've Learned

In this lesson, you've:

✅ **Created multiple tools** with different complexity levels  
✅ **Used parameters and type hints** to guide your agent  
✅ **Handled errors gracefully** in your tool implementations  
✅ **Seen tool selection in action** as your agent chooses the right tool  
✅ **Built a practical toolkit** for a personal assistant agent  

## Understanding Tool Integration

Your agent now demonstrates how Xaibo's architecture enables:

- **Automatic tool discovery**: New tools are immediately available
- **Intelligent selection**: The LLM chooses appropriate tools based on context
- **Seamless integration**: Tools feel like natural agent capabilities
- **Easy extension**: Adding new tools requires no configuration changes

## Next Steps

Your agent now has a powerful set of tools, but you might wonder how all these components work together. In the next lesson, [Understanding Protocols](understanding-protocols.md), you'll learn about Xaibo's protocol-based architecture and how it enables this flexibility.

Ready to understand the architecture that makes this possible? Continue with [Understanding Protocols](understanding-protocols.md)!