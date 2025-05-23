# Contributing to Xaibo

We welcome contributions to Xaibo! This guide will help you get started with contributing to the project.

---

## Getting Started

### Development Setup

#### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and pnpm (for UI development)
- Git

#### Clone the Repository

```bash
git clone https://github.com/xpressai/xaibo.git
cd xaibo
```

#### Set Up Development Environment

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies:**
   ```bash
   pip install -e ".[dev,webserver,openai,anthropic,google,bedrock,local]"
   ```

3. **Install pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Set up UI development (optional):**
   ```bash
   cd ui
   pnpm install
   cd ..
   ```

#### Verify Installation

```bash
# Run tests to verify setup
python -m pytest tests/ -v

# Start development server
python -m xaibo.server.web --agent-dir examples/google_calendar_example/agents
```

---

## Development Workflow

### Branch Strategy

We use a Git flow-based branching strategy:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Critical production fixes

### Creating a Feature Branch

```bash
# Update your local repository
git checkout develop
git pull origin develop

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "feat: add your feature description"

# Push your branch
git push origin feature/your-feature-name
```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

**Examples:**
```bash
git commit -m "feat(llm): add support for Google Gemini models"
git commit -m "fix(tools): handle timeout errors in MCP tool provider"
git commit -m "docs: update API reference for new protocols"
git commit -m "test(memory): add unit tests for vector memory module"
```

---

## Code Style and Standards

### Python Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

#### Configuration

The project includes configuration files:

```toml title="pyproject.toml"
[tool.black]
line-length = 88
target-version = ['py310']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.10"
strict = true
```

#### Running Code Quality Checks

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

#### Pre-commit Hooks

Pre-commit hooks automatically run these checks:

```yaml title=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

### Documentation Style

- Use clear, concise language
- Include code examples for all features
- Follow the existing documentation structure
- Use proper Markdown formatting
- Include type hints in code examples

### TypeScript/JavaScript Style (UI)

For UI development:

```bash
cd ui
pnpm run lint    # ESLint
pnpm run format  # Prettier
pnpm run check   # Svelte check
```

---

## Testing Requirements and Procedures

### Test Structure

```
tests/
├── core/           # Core functionality tests
├── llms/           # LLM module tests
├── memory/         # Memory module tests
├── tools/          # Tool provider tests
├── webserver/      # Web server tests
├── agents/         # Agent integration tests
└── resources/      # Test resources and fixtures
```

### Writing Tests

#### Unit Tests

```python title="tests/example_test.py"
import pytest
from unittest.mock import Mock, patch
from xaibo.primitives.modules.llm.openai import OpenAILLM

class TestOpenAILLM:
    @pytest.fixture
    def llm(self):
        return OpenAILLM(model="gpt-3.5-turbo", api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_generate_success(self, llm):
        """Test successful LLM generation"""
        with patch('openai.AsyncOpenAI') as mock_client:
            # Setup mock
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            # Test
            messages = [{"role": "user", "content": "Hello"}]
            result = await llm.generate(messages)
            
            # Assertions
            assert result.content == "Test response"
            assert result.model == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_generate_api_error(self, llm):
        """Test LLM generation with API error"""
        with patch('openai.AsyncOpenAI') as mock_client:
            # Setup mock to raise exception
            mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")
            
            # Test
            messages = [{"role": "user", "content": "Hello"}]
            
            # Should raise exception
            with pytest.raises(Exception, match="API Error"):
                await llm.generate(messages)
```

#### Integration Tests

```python title="tests/integration_test.py"
import pytest
from xaibo import Xaibo
from xaibo.core.config import AgentConfig

class TestAgentIntegration:
    @pytest.fixture
    def agent_config(self):
        return AgentConfig(
            id="test-agent",
            modules=[
                {
                    "module": "xaibo.primitives.modules.llm.MockLLM",
                    "id": "llm",
                    "config": {
                        "responses": [{"content": "Mock response", "model": "mock"}]
                    }
                }
            ]
        )
    
    @pytest.mark.asyncio
    async def test_agent_execution(self, agent_config):
        """Test complete agent execution"""
        xaibo = Xaibo()
        agent = xaibo.register_agent(agent_config)
        
        # Test agent execution
        response = await agent.handle_text_message("Hello")
        
        assert response is not None
        assert "Mock response" in str(response)
```

#### Test Fixtures

```python title="tests/conftest.py"
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_agent_config():
    """Provide a sample agent configuration"""
    return {
        "id": "test-agent",
        "description": "Test agent",
        "modules": [
            {
                "module": "xaibo.primitives.modules.llm.MockLLM",
                "id": "llm",
                "config": {"responses": [{"content": "Test", "model": "mock"}]}
            }
        ]
    }

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["XAIBO_LOG_LEVEL"] = "DEBUG"
    os.environ["XAIBO_DEBUG"] = "true"
    yield
    # Cleanup if needed
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/llms/test_openai.py

# Run with coverage
python -m pytest --cov=src/xaibo --cov-report=html

# Run tests with specific markers
python -m pytest -m "not slow"

# Run tests in parallel
python -m pytest -n auto
```

### Test Configuration

```ini title="pytest.ini"
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
```

### Mocking Guidelines

1. **Mock external dependencies:**
   ```python
   @patch('requests.get')
   def test_api_call(self, mock_get):
       mock_get.return_value.json.return_value = {"result": "success"}
       # Test code here
   ```

2. **Use fixtures for common mocks:**
   ```python
   @pytest.fixture
   def mock_openai_client():
       with patch('openai.AsyncOpenAI') as mock:
           yield mock
   ```

3. **Mock file operations:**
   ```python
   @patch('builtins.open', mock_open(read_data="test data"))
   def test_file_operation(self):
       # Test code here
   ```

---

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   python -m pytest
   ```

2. **Run code quality checks:**
   ```bash
   black src/ tests/
   isort src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

3. **Update documentation if needed:**
   - Add docstrings to new functions/classes
   - Update relevant documentation files
   - Add examples for new features

4. **Add tests for new functionality:**
   - Unit tests for individual components
   - Integration tests for feature workflows
   - Update existing tests if behavior changes

### Pull Request Template

When creating a pull request, use this template:

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation made
- [ ] No new warnings introduced
- [ ] Added tests that prove the fix is effective or that the feature works

## Related Issues
Closes #(issue number)
```

### Review Process

1. **Automated Checks:**
   - CI/CD pipeline runs tests
   - Code quality checks
   - Security scans

2. **Manual Review:**
   - Code review by maintainers
   - Architecture review for significant changes
   - Documentation review

3. **Approval and Merge:**
   - At least one approval required
   - All checks must pass
   - Squash and merge preferred

---

## Project Structure and Architecture

### Core Architecture

```
src/xaibo/
├── core/                    # Core framework components
│   ├── protocols/          # Protocol interfaces
│   ├── models/             # Data models
│   ├── agent.py           # Agent implementation
│   ├── config.py          # Configuration handling
│   ├── exchange.py        # Dependency injection
│   └── registry.py        # Component registry
├── primitives/             # Built-in implementations
│   ├── modules/           # Module implementations
│   │   ├── llm/          # LLM providers
│   │   ├── memory/       # Memory systems
│   │   ├── tools/        # Tool providers
│   │   └── orchestrator/ # Orchestration logic
│   └── event_listeners/   # Event handling
├── server/                 # Web server and APIs
│   ├── adapters/          # API adapters
│   └── web.py            # Server implementation
└── cli/                   # Command-line interface
```

### Adding New Components

#### Creating a New Protocol

```python title="src/xaibo/core/protocols/my_protocol.py"
from abc import ABC, abstractmethod
from typing import Any

class MyProtocol(ABC):
    """Protocol for custom functionality"""
    
    @abstractmethod
    async def my_method(self, data: Any) -> Any:
        """Custom method description
        
        Args:
            data: Input data
            
        Returns:
            Processed result
        """
        pass
```

#### Implementing a Module

```python title="src/xaibo/primitives/modules/my_module.py"
from typing import Any
from xaibo.core.protocols.my_protocol import MyProtocol

class MyModule(MyProtocol):
    """Implementation of MyProtocol"""
    
    def __init__(self, config_param: str):
        self.config_param = config_param
    
    async def my_method(self, data: Any) -> Any:
        """Implementation of the protocol method"""
        # Implementation here
        return f"Processed: {data} with {self.config_param}"
```

#### Adding Tests

```python title="tests/modules/test_my_module.py"
import pytest
from xaibo.primitives.modules.my_module import MyModule

class TestMyModule:
    @pytest.fixture
    def module(self):
        return MyModule(config_param="test")
    
    @pytest.mark.asyncio
    async def test_my_method(self, module):
        result = await module.my_method("test_data")
        assert "Processed: test_data" in result
        assert "test" in result
```

### Documentation Guidelines

#### Code Documentation

```python
def example_function(param1: str, param2: int = 10) -> str:
    """Brief description of the function.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter with default value
        
    Returns:
        Description of the return value
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Example:
        >>> result = example_function("hello", 5)
        >>> print(result)
        "hello processed with 5"
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return f"{param1} processed with {param2}"
```

#### API Documentation

Use proper type hints and docstrings for all public APIs:

```python
from typing import List, Optional, Dict, Any

class APIClass:
    """Class for handling API operations.
    
    This class provides methods for interacting with external APIs
    and processing the responses.
    
    Attributes:
        base_url: The base URL for API requests
        timeout: Request timeout in seconds
    """
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
    
    async def fetch_data(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data from the API endpoint.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            List of data items from the API
            
        Raises:
            APIError: When the API request fails
            TimeoutError: When the request times out
        """
        # Implementation here
        pass
```

---

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our [Code of Conduct](https://github.com/xpressai/xaibo/blob/main/CODE_OF_CONDUCT.md).

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, and technical discussions
- **GitHub Discussions**: General questions and community discussions
- **Discord**: Real-time chat and community support
- **Email**: Direct contact with maintainers (hello@xpress.ai)

### Getting Help

1. **Check existing documentation** and examples
2. **Search GitHub issues** for similar problems
3. **Ask in Discord** for quick help
4. **Create a GitHub issue** for bugs or feature requests

### Reporting Issues

When reporting bugs, please include:

- **Environment details** (Python version, OS, Xaibo version)
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Error messages** and stack traces
- **Minimal code example** that demonstrates the issue

### Feature Requests

When requesting features:

- **Describe the use case** and motivation
- **Provide examples** of how it would be used
- **Consider backwards compatibility**
- **Discuss implementation approaches** if you have ideas

### Recognition

Contributors are recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributor graphs**
- **Discord contributor roles**

---

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist

1. **Update version numbers**
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Update documentation**
5. **Create release PR**
6. **Tag release**
7. **Publish to PyPI**
8. **Update documentation site**

### Development Releases

Development versions use the format: `X.Y.Z.devN`

```bash
# Install development version
pip install --pre xaibo
```

!!! tip "Contributing Tips"
    - Start with small contributions to get familiar with the codebase
    - Ask questions early and often - we're here to help!
    - Read existing code to understand patterns and conventions
    - Write tests for all new functionality
    - Keep pull requests focused and atomic

!!! note "Maintainer Notes"
    - Be responsive to contributor questions
    - Provide constructive feedback in reviews
    - Recognize and celebrate contributions
    - Keep the contribution process simple and welcoming

Thank you for contributing to Xaibo! Your contributions help make AI agent development more accessible and powerful for everyone.