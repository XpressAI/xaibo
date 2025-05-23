# Project Structure

Understanding how to organize Xaibo projects is crucial for building maintainable and scalable AI agent systems. This guide covers project organization patterns, file structures, and best practices for different project sizes.

---

## Basic Project Structure

When you initialize a new Xaibo project with `uvx xaibo init my_project`, you get this recommended structure:

```
my_project/
├── agents/                 # Agent configuration files
│   └── example.yml
├── modules/                # Custom module implementations
│   └── __init__.py
├── tools/                  # Tool implementations
│   ├── __init__.py
│   └── example.py
├── tests/                  # Test files
│   └── test_example.py
├── .env                    # Environment variables
└── pyproject.toml          # Project dependencies (if using uv)
```

### Directory Purposes

#### `agents/` Directory
Contains YAML configuration files that define your agents. Each file represents a complete agent configuration with modules, exchanges, and settings.

```yaml title="agents/example.yml"
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-3.5-turbo
  # ... more modules
```

#### `tools/` Directory
Houses Python tool implementations that can be used by agents. Tools are discovered automatically through the `PythonToolProvider`.

```python title="tools/example.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
```

#### `modules/` Directory
Contains custom module implementations when you need functionality beyond the built-in modules.

#### `tests/` Directory
Test files for your agents, tools, and custom modules.

---

## Scaling Project Structure

As your project grows, you'll want to organize it more systematically. Here are patterns for different project sizes:

### Medium Projects

```
my_project/
├── agents/
│   ├── customer_service/
│   │   ├── basic_support.yml
│   │   └── escalation_handler.yml
│   ├── data_analysis/
│   │   ├── report_generator.yml
│   │   └── trend_analyzer.yml
│   └── shared/
│       └── common_config.yml
├── tools/
│   ├── __init__.py
│   ├── customer/
│   │   ├── __init__.py
│   │   ├── crm_tools.py
│   │   └── ticket_tools.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database_tools.py
│   │   └── analytics_tools.py
│   └── shared/
│       ├── __init__.py
│       └── common_tools.py
├── modules/
│   ├── __init__.py
│   ├── custom_llm/
│   │   ├── __init__.py
│   │   └── specialized_llm.py
│   └── custom_memory/
│       ├── __init__.py
│       └── domain_memory.py
├── config/
│   ├── development.env
│   ├── staging.env
│   └── production.env
├── tests/
│   ├── agents/
│   ├── tools/
│   ├── modules/
│   └── integration/
└── docs/
    ├── agents.md
    ├── tools.md
    └── deployment.md
```

### Large Projects

```
enterprise_project/
├── agents/
│   ├── customer_service/
│   │   ├── tier1_support.yml
│   │   ├── tier2_support.yml
│   │   ├── escalation_manager.yml
│   │   └── feedback_analyzer.yml
│   ├── sales/
│   │   ├── lead_qualifier.yml
│   │   ├── proposal_generator.yml
│   │   └── follow_up_manager.yml
│   ├── operations/
│   │   ├── incident_responder.yml
│   │   ├── capacity_planner.yml
│   │   └── cost_optimizer.yml
│   └── shared/
│       ├── base_config.yml
│       └── common_modules.yml
├── src/
│   └── company_xaibo/
│       ├── __init__.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── customer/
│       │   ├── sales/
│       │   ├── operations/
│       │   └── integrations/
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── llm/
│       │   ├── memory/
│       │   ├── tools/
│       │   └── orchestrators/
│       ├── protocols/
│       │   ├── __init__.py
│       │   └── custom_protocols.py
│       └── utils/
│           ├── __init__.py
│           ├── config.py
│           └── monitoring.py
├── config/
│   ├── environments/
│   │   ├── dev.env
│   │   ├── staging.env
│   │   └── prod.env
│   ├── agents/
│   │   ├── customer_service.yml
│   │   ├── sales.yml
│   │   └── operations.yml
│   └── deployment/
│       ├── docker-compose.yml
│       └── kubernetes/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── performance/
├── docs/
│   ├── architecture/
│   ├── deployment/
│   ├── user_guides/
│   └── api_reference/
├── scripts/
│   ├── deploy.sh
│   ├── test.sh
│   └── setup.sh
└── monitoring/
    ├── dashboards/
    └── alerts/
```

---

## Configuration Organization

### Environment-Specific Configuration

Organize configuration files by environment:

```yaml title="config/base.yml"
# Base configuration shared across environments
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: ${LLM_MODEL}
      timeout: ${LLM_TIMEOUT:60.0}
```

```yaml title="config/development.yml"
# Development-specific overrides
extends: base.yml
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: llm
    config:
      responses: ["Development response"]
```

```yaml title="config/production.yml"
# Production-specific configuration
extends: base.yml
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      timeout: 120.0
```

### Shared Module Configurations

Create reusable module configurations:

```yaml title="agents/shared/llm_configs.yml"
# Shared LLM configurations
openai_gpt4: &openai_gpt4
  module: xaibo.primitives.modules.llm.OpenAILLM
  config:
    model: gpt-4
    temperature: 0.7

anthropic_claude: &anthropic_claude
  module: xaibo.primitives.modules.llm.AnthropicLLM
  config:
    model: claude-3-sonnet-20240229
    temperature: 0.7
```

```yaml title="agents/customer_service/support_agent.yml"
# Use shared configurations
id: support-agent
modules:
  - <<: *openai_gpt4
    id: llm
  # ... other modules
```

---

## Tool Organization Patterns

### Domain-Based Organization

Organize tools by business domain:

```python title="tools/customer/__init__.py"
"""Customer-related tools"""
from .crm_tools import *
from .support_tools import *
from .billing_tools import *
```

```python title="tools/customer/crm_tools.py"
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def get_customer_info(customer_id: str):
    """Retrieve customer information from CRM"""
    # Implementation
    pass

@tool
def update_customer_status(customer_id: str, status: str):
    """Update customer status in CRM"""
    # Implementation
    pass
```

### Functional Organization

Organize tools by functionality:

```python title="tools/data/database_tools.py"
@tool
def query_database(query: str, database: str = "main"):
    """Execute a database query"""
    # Implementation
    pass

@tool
def get_table_schema(table_name: str):
    """Get schema information for a table"""
    # Implementation
    pass
```

```python title="tools/communication/email_tools.py"
@tool
def send_email(to: str, subject: str, body: str):
    """Send an email"""
    # Implementation
    pass

@tool
def get_email_templates():
    """Get available email templates"""
    # Implementation
    pass
```

---

## Custom Module Development

### Module Structure

When creating custom modules, follow this structure:

```python title="modules/custom_llm/specialized_llm.py"
from typing import List
from xaibo.core.protocols.llm import LLMProtocol
from xaibo.core.models.llm import LLMResponse, Message

class SpecializedLLM(LLMProtocol):
    """Custom LLM with domain-specific optimizations"""
    
    def __init__(self, domain: str, base_llm: LLMProtocol):
        self.domain = domain
        self.base_llm = base_llm
        self.domain_prompts = self._load_domain_prompts()
    
    async def generate_response(self, messages: List[Message]) -> LLMResponse:
        # Add domain-specific context
        enhanced_messages = self._enhance_with_domain_context(messages)
        return await self.base_llm.generate_response(enhanced_messages)
    
    def supports_streaming(self) -> bool:
        return self.base_llm.supports_streaming()
    
    def _load_domain_prompts(self):
        # Load domain-specific prompts
        pass
    
    def _enhance_with_domain_context(self, messages: List[Message]):
        # Add domain context to messages
        pass
```

### Protocol Implementation

When implementing custom protocols:

```python title="modules/protocols/custom_protocols.py"
from abc import ABC, abstractmethod
from typing import Any, Dict

class CustomAnalyticsProtocol(ABC):
    """Protocol for analytics capabilities"""
    
    @abstractmethod
    async def track_event(self, event_name: str, properties: Dict[str, Any]):
        """Track an analytics event"""
        pass
    
    @abstractmethod
    async def get_metrics(self, metric_names: List[str]) -> Dict[str, float]:
        """Retrieve metric values"""
        pass
```

---

## Testing Organization

### Test Structure

Organize tests to mirror your source structure:

```
tests/
├── unit/
│   ├── tools/
│   │   ├── test_customer_tools.py
│   │   └── test_data_tools.py
│   ├── modules/
│   │   ├── test_custom_llm.py
│   │   └── test_custom_memory.py
│   └── agents/
│       └── test_agent_configs.py
├── integration/
│   ├── test_agent_workflows.py
│   └── test_tool_integration.py
├── e2e/
│   ├── test_customer_service_flow.py
│   └── test_sales_pipeline.py
└── fixtures/
    ├── mock_data.py
    └── test_configs/
```

### Test Configuration

Use separate configurations for testing:

```yaml title="tests/fixtures/test_configs/mock_agent.yml"
id: test-agent
modules:
  - module: xaibo.primitives.modules.llm.MockLLM
    id: llm
    config:
      responses: ["Test response"]
  - module: tests.fixtures.mock_tools.MockToolProvider
    id: tools
    config:
      tools: ["mock_tool"]
```

---

## Deployment Structure

### Docker Organization

```dockerfile title="Dockerfile"
FROM python:3.11-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN pip install uv && uv sync --frozen

# Copy source code
COPY src/ ./src/
COPY agents/ ./agents/
COPY config/ ./config/

# Set environment
ENV PYTHONPATH=/app/src

# Run the application
CMD ["uv", "run", "xaibo", "serve", "--config", "config/production.yml"]
```

### Kubernetes Configuration

```yaml title="deployment/kubernetes/agent-deployment.yml"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xaibo-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xaibo-agents
  template:
    metadata:
      labels:
        app: xaibo-agents
    spec:
      containers:
      - name: xaibo
        image: my-company/xaibo-agents:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
```

---

## Best Practices

### Configuration Management

!!! tip "Configuration Guidelines"
    - Use environment variables for secrets and environment-specific values
    - Keep base configurations DRY with YAML anchors and references
    - Validate configurations at startup
    - Document all configuration options

### Code Organization

!!! tip "Code Structure Guidelines"
    - Group related functionality together
    - Use clear, descriptive names for modules and tools
    - Implement proper error handling and logging
    - Follow Python packaging conventions

### Testing Strategy

!!! tip "Testing Guidelines"
    - Test each component in isolation
    - Use mocks for external dependencies
    - Include integration tests for critical workflows
    - Maintain test data fixtures separately

### Documentation

!!! tip "Documentation Guidelines"
    - Document agent configurations and their purposes
    - Include examples for custom modules and tools
    - Maintain deployment and operational documentation
    - Keep API documentation up to date

---

## Framework Architecture

Understanding Xaibo's internal structure helps when building larger projects:

```
xaibo/
├── core/                   # Core framework components
│   ├── agent.py           # Agent orchestration
│   ├── config.py          # Configuration management
│   ├── exchange.py        # Dependency injection
│   ├── registry.py        # Component registry
│   ├── protocols/         # Protocol definitions
│   └── models/            # Data models
├── primitives/            # Built-in implementations
│   ├── modules/           # Standard modules
│   │   ├── llm/          # LLM implementations
│   │   ├── memory/       # Memory implementations
│   │   ├── tools/        # Tool providers
│   │   └── orchestrator/ # Orchestrators
│   └── event_listeners/   # Event handling
├── server/                # Web server components
│   ├── web.py            # Main server
│   └── adapters/         # API adapters
└── cli/                   # Command-line interface
```

This structure informs how you should organize your own projects and where to place custom implementations.

---

## Next Steps

With a solid understanding of project structure:

- **[Getting Started](getting-started.md)**: Build your first project
- **[Core Concepts](core-concepts.md)**: Understand the architectural foundations
- **[Features](features.md)**: Explore advanced capabilities

Proper project organization is key to building maintainable and scalable AI agent systems with Xaibo.