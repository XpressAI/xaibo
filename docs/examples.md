# Examples and Tutorials

This page provides comprehensive examples and tutorials to help you build powerful AI agents with Xaibo. From basic setups to advanced integrations, these examples demonstrate real-world use cases and best practices.

---

## Basic Examples

### Simple Echo Agent

Let's start with the simplest possible agent that echoes user input:

```yaml title="agents/echo.yml"
id: echo-agent
description: A simple agent that echoes user input
modules:
  - module: xaibo_examples.echo.Echo
    id: echo
    config:
      prefix: "You said: "
```

This minimal configuration demonstrates Xaibo's automatic exchange inference - the framework automatically connects the Echo module to the response handler.

### Time Tool Agent

Here's a practical agent that can tell you the current time:

```yaml title="agents/time-agent.yml"
id: time-agent
description: An agent that can tell the current time
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: python-tools
    config:
      tool_packages: [tools.time_tools]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 5
      system_prompt: |
        You are a helpful assistant that can tell the current time.
        Use the available tools to answer user questions.
```

```python title="tools/time_tools.py"
from datetime import datetime, timezone
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    """Gets the current time in UTC"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

@tool
def current_time_in_timezone(timezone_name: str):
    """Gets the current time in a specific timezone
    
    Args:
        timezone_name: The timezone name (e.g., 'US/Pacific', 'Europe/London')
    """
    import zoneinfo
    try:
        tz = zoneinfo.ZoneInfo(timezone_name)
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: Invalid timezone '{timezone_name}'. {str(e)}"
```

---

## Real-World Use Cases

### Google Calendar Integration

This example shows how to build an agent that can interact with Google Calendar:

```yaml title="agents/calendar-agent.yml"
id: calendar-agent
description: An agent that can manage Google Calendar events
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      temperature: 0.1
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: calendar-tools
    config:
      tool_packages: [tools.calendar_tools]
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "./data/calendar_memory.pkl"
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 512
      window_overlap: 50
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: text-embedding-ada-002
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./data/calendar_vectors"
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      system_prompt: |
        You are a helpful calendar assistant that can manage Google Calendar events.
        You can create, read, update, and delete calendar events.
        Always confirm important actions with the user before executing them.
```

```python title="tools/calendar_tools.py"
from datetime import datetime, timedelta
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from xaibo.primitives.modules.tools.python_tool_provider import tool

# Initialize Google Calendar service
def get_calendar_service():
    """Initialize Google Calendar API service"""
    # This would typically load credentials from a secure location
    # For this example, we'll assume credentials are properly configured
    creds = Credentials.from_authorized_user_file('token.json')
    return build('calendar', 'v3', credentials=creds)

@tool
def list_upcoming_events(max_results: int = 10):
    """List upcoming calendar events
    
    Args:
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        service = get_calendar_service()
        now = datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No upcoming events found."
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append(f"- {event['summary']} at {start}")
        
        return "Upcoming events:\n" + "\n".join(event_list)
    
    except Exception as e:
        return f"Error retrieving events: {str(e)}"

@tool
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None
):
    """Create a new calendar event
    
    Args:
        title: Event title
        start_time: Start time in ISO format (e.g., '2024-01-15T10:00:00')
        end_time: End time in ISO format (e.g., '2024-01-15T11:00:00')
        description: Optional event description
        location: Optional event location
    """
    try:
        service = get_calendar_service()
        
        event = {
            'summary': title,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return f"Event created successfully: {created_event.get('htmlLink')}"
    
    except Exception as e:
        return f"Error creating event: {str(e)}"

@tool
def search_events(query: str, max_results: int = 10):
    """Search for calendar events by keyword
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
    """
    try:
        service = get_calendar_service()
        
        events_result = service.events().list(
            calendarId='primary',
            q=query,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found matching '{query}'."
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append(f"- {event['summary']} at {start}")
        
        return f"Events matching '{query}':\n" + "\n".join(event_list)
    
    except Exception as e:
        return f"Error searching events: {str(e)}"
```

### Database Integration Agent

An agent that can interact with databases to answer questions about data:

```yaml title="agents/database-agent.yml"
id: database-agent
description: An agent that can query and analyze database data
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      temperature: 0
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: db-tools
    config:
      tool_packages: [tools.database_tools]
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 15
      system_prompt: |
        You are a data analyst assistant that can query databases to answer questions.
        Always be careful with database operations and explain your queries.
        When writing SQL, use proper formatting and include comments.
```

```python title="tools/database_tools.py"
import sqlite3
import pandas as pd
from typing import List, Dict, Any
from xaibo.primitives.modules.tools.python_tool_provider import tool

DATABASE_PATH = "./data/example.db"

@tool
def execute_sql_query(query: str):
    """Execute a SQL query and return results
    
    Args:
        query: SQL query to execute (SELECT statements only for safety)
    """
    try:
        # Safety check - only allow SELECT statements
        if not query.strip().upper().startswith('SELECT'):
            return "Error: Only SELECT queries are allowed for safety."
        
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return "Query executed successfully but returned no results."
        
        # Format results nicely
        result = f"Query returned {len(df)} rows:\n\n"
        result += df.to_string(index=False, max_rows=20)
        
        if len(df) > 20:
            result += f"\n\n... and {len(df) - 20} more rows"
        
        return result
    
    except Exception as e:
        return f"Error executing query: {str(e)}"

@tool
def describe_table(table_name: str):
    """Get information about a database table structure
    
    Args:
        table_name: Name of the table to describe
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            return f"Table '{table_name}' not found."
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        conn.close()
        
        result = f"Table: {table_name}\n"
        result += f"Rows: {row_count}\n\n"
        result += "Columns:\n"
        
        for col in columns:
            result += f"  - {col[1]} ({col[2]})"
            if col[3]:  # NOT NULL
                result += " NOT NULL"
            if col[5]:  # PRIMARY KEY
                result += " PRIMARY KEY"
            result += "\n"
        
        return result
    
    except Exception as e:
        return f"Error describing table: {str(e)}"

@tool
def list_tables():
    """List all tables in the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        conn.close()
        
        if not tables:
            return "No tables found in the database."
        
        table_list = [table[0] for table in tables]
        return "Available tables:\n" + "\n".join(f"  - {table}" for table in table_list)
    
    except Exception as e:
        return f"Error listing tables: {str(e)}"

@tool
def get_sample_data(table_name: str, limit: int = 5):
    """Get sample data from a table
    
    Args:
        table_name: Name of the table
        limit: Number of sample rows to return (default: 5)
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
        conn.close()
        
        if df.empty:
            return f"Table '{table_name}' is empty."
        
        return f"Sample data from {table_name}:\n\n" + df.to_string(index=False)
    
    except Exception as e:
        return f"Error getting sample data: {str(e)}"
```

---

## Advanced Configuration Patterns

### Multi-LLM Agent with Fallback

This example shows how to use multiple LLMs with fallback capabilities:

```yaml title="agents/multi-llm-agent.yml"
id: multi-llm-agent
description: An agent with multiple LLM providers and fallback
modules:
  # Primary LLM (OpenAI GPT-4)
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: primary-llm
    config:
      model: gpt-4
      timeout: 30.0
  
  # Fallback LLM (Anthropic Claude)
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: fallback-llm
    config:
      model: claude-3-sonnet-20240229
      timeout: 30.0
  
  # LLM Combinator for fallback logic
  - module: xaibo.primitives.modules.llm.LLMCombinator
    id: combined-llm
    config:
      prompts:
        - "You are a helpful assistant. Respond concisely and accurately."
        - "You are a helpful assistant. If the primary model failed, provide a reliable response."
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.general_tools]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10

exchange:
  # Connect combinator to both LLMs
  - module: combined-llm
    protocol: LLMProtocol
    provider: [primary-llm, fallback-llm]
  
  # Connect orchestrator to combined LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: combined-llm
  
  # Set entry point
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

### Memory-Enhanced Agent

An agent with sophisticated memory capabilities:

```yaml title="agents/memory-agent.yml"
id: memory-agent
description: An agent with advanced memory capabilities
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
  
  # Memory system components
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: "./data/agent_memory.pkl"
  
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 1024
      window_overlap: 100
      encoding_name: "cl100k_base"
  
  - module: xaibo.primitives.modules.memory.SentenceTransformerEmbedder
    id: embedder
    config:
      model_name: "all-MiniLM-L6-v2"
      model_kwargs:
        device: "cpu"
        cache_folder: "./models/sentence-transformers"
  
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: "./data/memory_vectors"
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.memory_tools]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 15
      system_prompt: |
        You are an intelligent assistant with long-term memory capabilities.
        You can remember information from previous conversations and use it to provide better assistance.
        Use the memory tools to store and retrieve important information.

exchange:
  # Connect memory system
  - module: memory
    protocol: ChunkerProtocol
    provider: chunker
  - module: memory
    protocol: EmbedderProtocol
    provider: embedder
  - module: memory
    protocol: VectorIndexProtocol
    provider: vector_index
  
  # Connect orchestrator to memory and LLM
  - module: orchestrator
    protocol: LLMProtocol
    provider: llm
  - module: orchestrator
    protocol: MemoryProtocol
    provider: memory
  
  # Set entry point
  - module: __entry__
    protocol: TextMessageHandlerProtocol
    provider: orchestrator
```

```python title="tools/memory_tools.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def remember_information(information: str, category: str = "general"):
    """Store information in long-term memory
    
    Args:
        information: The information to remember
        category: Category for organizing the information
    """
    # This would integrate with the memory system
    # For now, we'll return a confirmation
    return f"Remembered: {information} (Category: {category})"

@tool
def recall_information(query: str, max_results: int = 5):
    """Recall information from memory based on a query
    
    Args:
        query: What to search for in memory
        max_results: Maximum number of results to return
    """
    # This would query the vector memory system
    # For now, we'll return a placeholder
    return f"Searching memory for: {query} (returning up to {max_results} results)"
```

---

## Integration Examples

### API Integration Agent

An agent that can interact with external APIs:

```python title="tools/api_tools.py"
import requests
import json
from typing import Dict, Any, Optional
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def make_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None
):
    """Make an HTTP request to an external API
    
    Args:
        url: The URL to request
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Optional headers dictionary
        data: Optional data for POST/PUT requests
    """
    try:
        method = method.upper()
        
        if headers is None:
            headers = {}
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return f"Unsupported HTTP method: {method}"
        
        response.raise_for_status()
        
        try:
            return {
                "status_code": response.status_code,
                "data": response.json()
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": response.text
            }
    
    except requests.exceptions.RequestException as e:
        return f"HTTP request failed: {str(e)}"

@tool
def get_weather(city: str, api_key: str):
    """Get weather information for a city
    
    Args:
        city: City name
        api_key: OpenWeatherMap API key
    """
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        weather = data["weather"][0]
        main = data["main"]
        
        return f"""Weather in {city}:
- Condition: {weather['description'].title()}
- Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)
- Humidity: {main['humidity']}%
- Pressure: {main['pressure']} hPa"""
    
    except Exception as e:
        return f"Error getting weather data: {str(e)}"
```

### File Processing Agent

An agent that can process various file types:

```python title="tools/file_tools.py"
import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def read_text_file(file_path: str):
    """Read content from a text file
    
    Args:
        file_path: Path to the text file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return f"File content ({len(content)} characters):\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def read_csv_file(file_path: str, max_rows: int = 10):
    """Read and display CSV file content
    
    Args:
        file_path: Path to the CSV file
        max_rows: Maximum number of rows to display
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        if not rows:
            return "CSV file is empty."
        
        result = f"CSV file with {len(rows)} rows and {len(rows[0])} columns:\n\n"
        result += "Columns: " + ", ".join(rows[0].keys()) + "\n\n"
        
        display_rows = rows[:max_rows]
        for i, row in enumerate(display_rows, 1):
            result += f"Row {i}: {dict(row)}\n"
        
        if len(rows) > max_rows:
            result += f"\n... and {len(rows) - max_rows} more rows"
        
        return result
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

@tool
def read_json_file(file_path: str):
    """Read and parse JSON file content
    
    Args:
        file_path: Path to the JSON file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        return f"JSON file content:\n\n{json.dumps(data, indent=2)}"
    except Exception as e:
        return f"Error reading JSON file: {str(e)}"

@tool
def list_directory_contents(directory_path: str):
    """List contents of a directory
    
    Args:
        directory_path: Path to the directory
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return f"Directory does not exist: {directory_path}"
        
        if not path.is_dir():
            return f"Path is not a directory: {directory_path}"
        
        contents = []
        for item in path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                contents.append(f"📄 {item.name} ({size} bytes)")
            elif item.is_dir():
                contents.append(f"📁 {item.name}/")
        
        if not contents:
            return f"Directory is empty: {directory_path}"
        
        return f"Contents of {directory_path}:\n" + "\n".join(contents)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@tool
def write_text_file(file_path: str, content: str):
    """Write content to a text file
    
    Args:
        file_path: Path where to write the file
        content: Content to write
    """
    try:
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return f"Successfully wrote {len(content)} characters to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
```

---

## Testing Your Agents

### Unit Testing Tools

```python title="tests/test_agent_tools.py"
import pytest
from unittest.mock import Mock, patch
from tools.time_tools import current_time, current_time_in_timezone

def test_current_time():
    """Test the current_time tool"""
    result = current_time()
    assert "UTC" in result
    assert len(result.split()) >= 3  # Should contain date, time, and timezone

def test_current_time_in_timezone():
    """Test timezone-specific time tool"""
    result = current_time_in_timezone("US/Pacific")
    assert "PST" in result or "PDT" in result
    
    # Test invalid timezone
    result = current_time_in_timezone("Invalid/Timezone")
    assert "Error" in result

@patch('tools.database_tools.sqlite3.connect')
def test_database_query(mock_connect):
    """Test database query tool with mocked database"""
    from tools.database_tools import execute_sql_query
    
    # Mock database connection and cursor
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Test successful query
    result = execute_sql_query("SELECT * FROM users")
    assert "Error" not in result
    
    # Test invalid query (non-SELECT)
    result = execute_sql_query("DROP TABLE users")
    assert "Error" in result
    assert "Only SELECT queries are allowed" in result
```

### Integration Testing

```python title="tests/test_agent_integration.py"
import pytest
from xaibo.core.xaibo import Xaibo
from xaibo.core.config import AgentConfig

@pytest.fixture
def xaibo_instance():
    """Create a Xaibo instance for testing"""
    return Xaibo()

@pytest.fixture
def test_agent_config():
    """Create a test agent configuration"""
    return AgentConfig.from_yaml_file("agents/echo.yml")

def test_agent_loading(xaibo_instance, test_agent_config):
    """Test that agents can be loaded correctly"""
    agent = xaibo_instance.create_agent(test_agent_config)
    assert agent is not None
    assert agent.id == test_agent_config.id

@pytest.mark.asyncio
async def test_agent_response(xaibo_instance, test_agent_config):
    """Test that agents can process messages and return responses"""
    agent = xaibo_instance.create_agent(test_agent_config)
    
    response = await agent.handle_text_message("Hello, world!")
    assert response is not None
    assert "Hello, world!" in response.content
```

---

## Best Practices

### Configuration Management

1. **Use Environment Variables**: Store sensitive information like API keys in environment variables:

```yaml title="agents/production-agent.yml"
id: production-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}  # Environment variable
      timeout: 60.0
```

2. **Organize by Environment**: Create different configurations for different environments:

```
agents/
├── development/
│   └── dev-agent.yml
├── staging/
│   └── staging-agent.yml
└── production/
    └── prod-agent.yml
```

### Error Handling

Always implement proper error handling in your tools:

```python
@tool
def safe_api_call(url: str):
    """Example of proper error handling in tools"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return "Error: Request timed out"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
```

### Performance Optimization

1. **Use Appropriate Memory Settings**: Configure memory components based on your use case
2. **Set Reasonable Timeouts**: Prevent hanging requests with appropriate timeout values
3. **Limit Tool Iterations**: Use `max_thoughts` to prevent infinite loops

### Security Considerations

1. **Validate Tool Inputs**: Always validate and sanitize tool inputs
2. **Limit File Access**: Restrict file operations to specific directories
3. **Use Read-Only Database Connections**: For database tools, use read-only connections when possible
4. **Sanitize SQL Queries**: Prevent SQL injection by using parameterized queries

---

!!! tip "Next Steps"
    - Explore the [API Reference](api-reference.md) for detailed module documentation
    - Learn about [deployment strategies](deployment.md) for production use
    - Check out the [troubleshooting guide](troubleshooting.md) for common issues