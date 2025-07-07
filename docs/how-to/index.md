# How-to Guides

How-to guides provide step-by-step instructions for solving specific problems with Xaibo. Each guide focuses on accomplishing a particular goal and assumes you have basic familiarity with Xaibo concepts.

## Installation and Setup

- [How to install Xaibo with different dependency groups](installation.md) - Install Xaibo with only the dependencies you need

## Security

- [How to set up authentication](authentication.md) - Secure your Xaibo server with API key authentication for OpenAI and MCP adapters

## Tools Integration

- [How to create and integrate Python tools](tools/python-tools.md) - Add custom Python functions as agent tools
- [How to integrate MCP (Model Context Protocol) tools](tools/mcp-tools.md) - Connect external MCP servers to your agents

## Integrations

- [How to use Xaibo agents in LiveKit voice assistants](integrations/livekit-voice-assistant.md) - Create real-time conversational AI applications with LiveKit

## LLM Configuration

- [How to switch between different LLM providers](llm/switch-providers.md) - Configure agents to use OpenAI, Anthropic, Google, or AWS Bedrock

## Orchestrator Configuration

- [How to switch from other orchestrators to ReAct pattern](orchestrator/switch-to-react-pattern.md) - Migrate to ReActOrchestrator for structured reasoning
- [How to customize ReAct reasoning prompts](orchestrator/customize-react-prompts.md) - Control how your agent thinks, acts, and observes
- [How to debug agent reasoning with visual indicators](orchestrator/debug-agent-reasoning.md) - Use visual feedback to optimize agent behavior
- [How to handle complex multi-tool workflows](orchestrator/handle-complex-workflows.md) - Manage sophisticated multi-step processes

## Memory and Storage

- [How to set up vector memory for agents](memory/setup-vector-memory.md) - Enable agents to store and retrieve information using vector embeddings

## Deployment

- [How to deploy with OpenAI-compatible API](deployment/openai-api.md) - Expose your agents through an OpenAI-compatible REST API
- [How to deploy as an MCP server](deployment/mcp-server.md) - Make your agents available as MCP tools for other applications
- [How to start the OpenAI Responses API (Quickstart)](api/openai-responses-quickstart.md) - Get the OpenAI Responses API running in 2 minutes

## Examples

Explore complete working examples that demonstrate Xaibo in action:

- [Google Calendar Example](https://github.com/xpressai/xaibo/tree/main/examples/google_calendar_example) - Build an agent that can read and create calendar events using Google Calendar API
- [LiveKit Voice Assistant Example](https://github.com/xpressai/xaibo/tree/main/examples/livekit_example) - Create a real-time voice assistant using LiveKit for speech-to-text and text-to-speech

## Getting Help

If you encounter issues while following these guides:

1. Check the [troubleshooting section](../reference/troubleshooting.md) in the reference documentation
2. Review the [tutorial](../tutorial/index.md) for foundational concepts
3. Join our [Discord community](https://discord.gg/uASMzSSVKe) for support
4. Report bugs on [GitHub](https://github.com/xpressai/xaibo/issues)