import argparse

from pathlib import Path
from shutil import which
import subprocess, shlex, sys, os

import questionary

from xaibo import Xaibo, __version__
try:
    from xaibo.server.web import XaiboWebServer
except ImportError as e:
    XaiboWebServer = None

def universal_run(command, *, timeout=None, text=True, env=None, cwd=None):
    """
    Cross‑platform command runner.
    - command: list or string (space‑separated)
    - env/cwd: Path objects accepted
    """
    if isinstance(command, str):
        command = shlex.split(command)
    exe = which(command[0]) or command[0]      # accept absolute path
    if not exe:
        raise FileNotFoundError(command[0])
    if isinstance(cwd, Path):
        cwd = str(cwd)
    cp = subprocess.run([exe, *command[1:]],
                        check=True, capture_output=False,
                        timeout=timeout, text=text,
                        env=env, cwd=cwd)
    return cp.stdout

def get_default_model_for_provider(provider):
    """
    Get the default model for a given LLM provider.
    
    Args:
        provider: The LLM provider name (e.g., 'openai', 'anthropic', 'google', 'bedrock')
        
    Returns:
        Tuple of (provider_class_name, default_model)
    """

    provider_configs = {
        'openai': ('OpenAILLM', 'gpt-4.1-nano'),  
        'anthropic': ('AnthropicLLM', 'claude-3-5-sonnet-20241022'), 
        'google': ('GoogleLLM', 'gemini-1.5-flash'),  
        'bedrock': ('BedrockLLM', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    }
    
    return provider_configs.get(provider, ('OpenAILLM', 'gpt-4o-mini'))

def select_primary_llm_provider(modules):
    """
    Select the primary LLM provider from the list of modules.
    Priority order: anthropic > google > bedrock > openai (default)
    
    Args:
        modules: List of selected module names
        
    Returns:
        Tuple of (provider_class_name, default_model)
    """
    # Define priority order (most capable/recommended first)
    priority_order = ['anthropic', 'google', 'bedrock', 'openai']
    
    for provider in priority_order:
        if provider in modules:
            return get_default_model_for_provider(provider)
    
    # Default fallback to OpenAI
    return get_default_model_for_provider('openai')

def generate_env_content(selected_modules):
    """
    Generate .env file content with only the environment variables that are actually used.
    
    Args:
        selected_modules: List of selected module names
        
    Returns:
        String containing the .env file content
    """
    content = []
    
    # Header
    content.append("# Xaibo Environment Configuration")
    content.append("# Configure the API keys for your selected providers")
    content.append("")
    
    # OpenAI Configuration - OPENAI_API_KEY is required by OpenAILLM and OpenAIEmbedder
    if "openai" in selected_modules:
        content.extend([
            "# OpenAI Configuration",
            "# Required for OpenAILLM and OpenAIEmbedder modules",
            "OPENAI_API_KEY=your_openai_api_key_here",
            ""
        ])
    
    # Anthropic Configuration - ANTHROPIC_API_KEY is required by AnthropicLLM
    if "anthropic" in selected_modules:
        content.extend([
            "# Anthropic Configuration",
            "# Required for AnthropicLLM module",
            "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
            ""
        ])
    
    # Google Configuration - GOOGLE_API_KEY is used by GoogleLLM
    if "google" in selected_modules:
        content.extend([
            "# Google AI Configuration",
            "# Required for GoogleLLM module",
            "GOOGLE_API_KEY=your_google_api_key_here",
            ""
        ])
    
    # AWS Bedrock Configuration - AWS credentials are required by BedrockLLM
    if "bedrock" in selected_modules:
        content.extend([
            "# AWS Bedrock Configuration",
            "# Required for BedrockLLM module",
            "AWS_ACCESS_KEY_ID=your_aws_access_key_id_here",
            "AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here",
            "AWS_DEFAULT_REGION=us-east-1",
            ""
        ])
    
    # Footer with instructions
    content.extend([
        "# Instructions:",
        "# 1. Replace the placeholder values above with your actual API keys",
        "# 2. Keep your API keys secure and never commit them to version control",
        "# 3. You can also set these as system environment variables instead"
    ])
    
    return "\n".join(content)

def init(args, extra_args=[]):
    """
    Initialize a Xaibo project folder from scratch.
    """
    modules = questionary.checkbox(
        "What dependencies do you want to include?", choices=[
            questionary.Choice(title="Webserver", value="webserver", description="The dependencies for running xaibo serve and xaibo dev", checked=True),
            questionary.Choice(title="OpenAI", value="openai", description="Allows using OpenAILLM and OpenAIEmbedder modules", checked=False),
            questionary.Choice(title="Anthropic", value="anthropic", description="Allows using AnthropicLLM module", checked=False),
            questionary.Choice(title="Google", value="google", description="Allows using GoogleLLM module", checked=False),
            questionary.Choice(title="Bedrock", value="bedrock", description="Allows using BedrockLLM module", checked=False),
            questionary.Choice(title="Local", value="local", description="Allows using local embeddings and memory modules", checked=False),
        ]
    ).ask()
    project_name = args.project_name
    curdir = Path(os.getcwd())
    project_dir = curdir / project_name
    universal_run(f"uv init {project_name}", cwd=curdir)
    universal_run(f"uv add xaibo xaibo[{','.join(modules)}] pytest", cwd=project_dir)

    (project_dir / "agents").mkdir()
    (project_dir / "modules").mkdir()
    (project_dir / "tools").mkdir()
    (project_dir / "tests").mkdir()

    (project_dir / "main.py").unlink()

    # Determine LLM provider and appropriate default model
    llm_provider, default_model = select_primary_llm_provider(modules)

    # Generate comprehensive .env file based on selected dependencies
    env_content = generate_env_content(modules)
    with (project_dir / ".env").open("w", encoding="utf-8") as f:
        f.write(env_content)
    
    # Add .env to .gitignore
    with (project_dir / ".gitignore").open("a", encoding="utf-8") as f:
        f.write(".env\n")



    with (project_dir / "agents" / "example.yml").open("w", encoding="utf-8") as f:
        f.write(
f"""
id: example
description: An example agent that uses tools
modules:
  - module: xaibo.primitives.modules.llm.{llm_provider}
    id: llm
    config:
      model: {default_model}
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
"""
        )

    with (project_dir / "modules" / "__init__.py").open("w", encoding="utf-8") as f:
        f.write("")

    with (project_dir / "tools" / "__init__.py").open("w", encoding="utf-8") as f:
        f.write("")


    with (project_dir / "tools" / "example.py").open("w", encoding="utf-8") as f:
        f.write(
f"""
from datetime import datetime, timezone, timedelta
from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def current_time():
    'Gets the current time in UTC'
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
"""
        )

    with (project_dir / "tests" / "test_example.py").open("w", encoding="utf-8") as f:
        f.write(
"""
import logging

import pytest
import os
from pathlib import Path
from xaibo import AgentConfig, Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.primitives.modules.conversation import SimpleConversation

from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_example_agent():
     # Load the stressing tool user config
    with open(r"./agents/example.yml") as f:
        content = f.read()
        config = AgentConfig.from_yaml(content)
    
    # Create registry and register agent
    xaibo = Xaibo()
    xaibo.register_agent(config)
    
    # Get agent instance
    agent = xaibo.get_agent_with("example", ConfigOverrides(
        instances={'history': SimpleConversation()},
        exchange=[ExchangeConfig(
            protocol='ConversationHistoryProtocol',
            provider='history'
        )]
    ))
    
    # Test with a prompt that should trigger the current_time tool
    response = await agent.handle_text("What time is it right now?")
    
    # Verify response contains time information
    assert "time" in response.text.lower()
"""
        )
    

    print(f"{project_name} initialized.")

def dev(args, extra_args=[]):
    """
    Start a Xaibo development session
    :return:
    """
    sys.path.append(os.getcwd())
    xaibo = Xaibo()

    server = XaiboWebServer(xaibo, ['xaibo.server.adapters.OpenAiApiAdapter'],'./agents', '127.0.0.1', 9001, True)
    server.start()


def serve(args, extra_args=[]):
    """
    Run Xaibo server with just the OpenAI API
    :return:
    """
    sys.path.append(os.getcwd())

    xaibo = Xaibo()

    server = XaiboWebServer(xaibo, ['xaibo.server.adapters.OpenAiApiAdapter'],'./agents', '0.0.0.0', 9001, False)
    server.start()


def main():
    parser = argparse.ArgumentParser(description='Xaibo Command Line Interface', add_help=True)
    parser.add_argument('--version', action='version', version=f'xaibo {__version__}')
    subparsers = parser.add_subparsers(dest="command")

    # 'init' command.
    init_parser = subparsers.add_parser('init', help='Initialize a Xaibo project')
    init_parser.add_argument('project_name', type=str, help='Name of the project')
    init_parser.set_defaults(func=init)

    # 'dev' command.
    dev_parser = subparsers.add_parser('dev', help='Start a Xaibo development session.')
    dev_parser.set_defaults(func=dev)

    # 'serve' command.
    serve_parser = subparsers.add_parser('serve', help='Run Xaibo server')
    serve_parser.set_defaults(func=serve)

    args, unknown_args = parser.parse_known_args()
    if hasattr(args, 'func'):
        args.func(args, unknown_args)
    else:
        valid_help_args = {"-h", "--h", "-help", "--help"}
        if any(arg in unknown_args for arg in valid_help_args):
            parser.print_help()


if __name__ == "__main__":
    main()
