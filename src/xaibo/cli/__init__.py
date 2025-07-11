import argparse

from pathlib import Path
from shutil import which
import subprocess, shlex, sys, os
import re
import shutil

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

def check_uv_version():
    """
    Check if uv is installed and meets the minimum version requirement (0.6.0).
    
    Raises:
        SystemExit: If uv is not installed or version is too old
    """
    try:
        # Check if uv is available
        if not which('uv'):
            print("Error: uv is not installed or not found in PATH.")
            print("Please install uv from https://docs.astral.sh/uv/getting-started/installation/")
            sys.exit(1)
        
        # Get uv version
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, check=True)
        version_output = result.stdout.strip()
        
        # Extract version number using regex (format: "uv 0.6.0" or similar)
        version_match = re.search(r'uv\s+(\d+\.\d+\.\d+)', version_output)
        if not version_match:
            print(f"Error: Could not parse uv version from output: {version_output}")
            sys.exit(1)
        
        version_str = version_match.group(1)
        version_parts = [int(x) for x in version_str.split('.')]
        
        # Check if version is at least 0.6.0
        min_version = [0, 6, 0]
        if version_parts < min_version:
            print(f"Error: uv version {version_str} is too old.")
            print("Please upgrade to uv 0.6.0 or later.")
            print("Run: pip install --upgrade uv")
            sys.exit(1)
                            
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to check uv version: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error while checking uv version: {e}")
        sys.exit(1)

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
    
    # LiveKit Configuration
    if "livekit" in selected_modules:
        content.extend([
            "# Livekit Configuration",
            "LIVEKIT_API_KEY=your_livekit_api_key_here",
            "LIVEKIT_API_SECRET=your_livekit_api_secret_here",
            "LIVEKIT_URL=your_livekit_url_here",
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

def get_modules_root():
    """Get the path to the primitives modules directory."""
    try:
        import xaibo.primitives.modules
        return Path(xaibo.primitives.modules.__file__).parent
    except ImportError:
        raise ImportError("Could not find xaibo.primitives.modules")

def list_top_level_packages():
    """List all top-level packages in the primitives modules directory."""
    modules_root = get_modules_root()
    return sorted(p.name for p in modules_root.iterdir() if p.is_dir() and not p.name.startswith('__'))

def list_module_contents(pkg_name: str):
    """List contents of a specific package."""
    modules_root = get_modules_root()
    pkg_path = modules_root / pkg_name
    items = []
    for p in sorted(pkg_path.iterdir()):
        if p.name == "__init__.py":
            continue
        display = p.name[:-3] if p.suffix == ".py" else p.name
        items.append((display, p))
    return dict(items)  # map display → Path

def resolve_item(arg: str):
    """
    Given an arg like 'memory.memory_provider' or just 'memory_provider',
    return the (package, Path) tuple.
    """
    if "." in arg:
        pkg, item = arg.split(".", 1)
        contents = list_module_contents(pkg)
        if item not in contents:
            raise FileNotFoundError(f"No item {item!r} in package {pkg!r}")
        return pkg, contents[item]
    else:
        # search every package for a matching item
        matches = []
        for pkg in list_top_level_packages():
            contents = list_module_contents(pkg)
            if arg in contents:
                matches.append((pkg, contents[arg]))
        if not matches:
            raise FileNotFoundError(f"No item named {arg!r} in any package")
        if len(matches) > 1:
            pkgs = ", ".join(p for p,_ in matches)
            raise ValueError(f"Ambiguous item {arg!r} found in: {pkgs}")
        return matches[0]

def ensure_init_py(directory: Path):
    """Ensure __init__.py exists in the given directory."""
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Auto-generated __init__.py\n")

def eject_items(items_with_packages, dest_root: Path):
    """
    Eject the specified items to the destination with proper package structure.
    
    Args:
        items_with_packages: List of (package_name, source_path) tuples
        dest_root: Root destination directory
    """
    # Ensure modules directory exists
    modules_dir = dest_root / "modules"
    modules_dir.mkdir(exist_ok=True)
    ensure_init_py(modules_dir)
    
    for pkg_name, src_path in items_with_packages:
        # Create package directory
        pkg_dir = modules_dir / pkg_name
        pkg_dir.mkdir(exist_ok=True)
        ensure_init_py(pkg_dir)
        
        # Determine destination path
        dst_path = pkg_dir / src_path.name
        
        if dst_path.exists():
            print(f"⚠️ Skipping {pkg_name}.{src_path.name}; already exists.")
            continue
        
        # Copy the file or directory
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)
        
        print(f"✅ Ejected {pkg_name}.{src_path.name} → {dst_path.relative_to(dest_root)}")

def interactive_eject_mode(dest: Path):
    """Interactive mode for ejecting modules."""
    pkg = questionary.select("What do you want to eject?", list_top_level_packages()).ask()
    if not pkg:
        return
    
    items = questionary.checkbox(
        f"{pkg} — which item(s) do you want?",
        choices=[questionary.Choice(k, v) for k,v in list_module_contents(pkg).items()]
    ).ask()
    
    if items:
        # Convert to (package, path) tuples
        items_with_packages = [(pkg, item) for item in items]
        eject_items(items_with_packages, dest)

def init(args, extra_args=[]):
    """
    Initialize a Xaibo project folder from scratch.
    """
    # Check uv version before proceeding
    check_uv_version()
    
    modules = questionary.checkbox(
        "What dependencies do you want to include?", choices=[
            questionary.Choice(title="Webserver", value="webserver", description="The dependencies for running xaibo serve and xaibo dev", checked=True),
            questionary.Choice(title="OpenAI", value="openai", description="Allows using OpenAILLM and OpenAIEmbedder modules", checked=False),
            questionary.Choice(title="Anthropic", value="anthropic", description="Allows using AnthropicLLM module", checked=False),
            questionary.Choice(title="Google", value="google", description="Allows using GoogleLLM module", checked=False),
            questionary.Choice(title="Bedrock", value="bedrock", description="Allows using BedrockLLM module", checked=False),
            questionary.Choice(title="Local", value="local", description="Allows using local embeddings and memory modules", checked=False),
            questionary.Choice(title="LiveKit", value="livekit", description="Allows using LiveKit integration", checked=False),
        ]
    ).ask()
    project_name = args.project_name
    curdir = Path(os.getcwd())
    project_dir = curdir / project_name
    universal_run(f"uv init --bare {project_name}", cwd=curdir)
    universal_run(f"uv add xaibo xaibo[{','.join(modules)}] pytest", cwd=project_dir)

    (project_dir / "agents").mkdir()
    (project_dir / "modules").mkdir()
    (project_dir / "tools").mkdir()
    (project_dir / "tests").mkdir()

    # Determine LLM provider and appropriate default model
    llm_provider, default_model = select_primary_llm_provider(modules)

    # Generate comprehensive .env file based on selected dependencies
    env_content = generate_env_content(modules)
    with (project_dir / ".env").open("w", encoding="utf-8") as f:
        f.write(env_content)
    
    # Add .env and debug/ to .gitignore
    with (project_dir / ".gitignore").open("a", encoding="utf-8") as f:
        f.write(".env\n")
        f.write("debug/\n")



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
  - module: xaibo.primitives.modules.orchestrator.SimpleToolOrchestrator
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
     # Load the simple tool orchestrator config
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

def eject(args, extra_args=[]):
    """
    Eject primitive modules into the current project.
    """
    # If user ran `eject list`, list everything and exit
    if args.action == 'list':
        print("Available packages and their ejectable items:\n")
        for pkg in list_top_level_packages():
            print(f"- {pkg}:")
            for item in sorted(list_module_contents(pkg).keys()):
                print(f"    • {item}")
        return

    # Otherwise, perform an eject (interactive or via -m)
    dest = Path(args.dest) if args.dest else Path.cwd()
    if args.module:
        # Non-interactive: resolve each module and eject
        try:
            items_with_packages = [resolve_item(arg) for arg in args.module]
            eject_items(items_with_packages, dest)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return
    else:
        # Interactive mode
        interactive_eject_mode(dest)

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

    # 'eject' command
    eject_parser = subparsers.add_parser('eject', help='Eject primitive modules')
    eject_parser.add_argument('action', nargs='?', choices=['list'],
                             help="If `list`, show all available items to eject")
    eject_parser.add_argument("-m", "--module", nargs="+",
                             help="Which module(s) to eject; use 'pkg.item' or just 'item'")
    eject_parser.add_argument("-d", "--dest", type=str, default=None,
                             help="Destination directory (default: current directory)")
    eject_parser.set_defaults(func=eject)

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
