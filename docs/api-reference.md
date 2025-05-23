# API Reference

This comprehensive API reference covers all the interfaces, modules, and endpoints available in Xaibo.

## Quick Navigation

- **[Protocol Interfaces](api/protocols.md)** - Core protocols that define component interfaces
- **[Module APIs](api/modules.md)** - Available modules and their configurations
- **[Server APIs](api/server.md)** - HTTP endpoints and server configuration
- **[Event System](api/events.md)** - Event listeners and monitoring capabilities

## Overview

Xaibo's API is organized around several key concepts:

### Protocol-Based Architecture
Xaibo uses protocol interfaces to define clear boundaries between components. This enables dependency injection and makes the system highly modular and testable.

### Module System
All functionality is provided through modules that implement specific protocols. This includes LLM providers, tool integrations, memory systems, and more.

### Server Adapters
Xaibo can expose different API interfaces through server adapters, including OpenAI-compatible endpoints and MCP (Model Context Protocol) support.

### Event System
A comprehensive event system allows monitoring and debugging of all agent operations, from tool calls to LLM interactions.

## Getting Started with the API

1. **Define Protocols** - Start by understanding the [protocol interfaces](api/protocols.md) that define how components interact
2. **Configure Modules** - Set up your agent using the available [modules](api/modules.md)
3. **Expose APIs** - Use [server adapters](api/server.md) to make your agent accessible via HTTP
4. **Monitor Operations** - Implement [event listeners](api/events.md) to observe agent behavior

For complete examples and tutorials, see the [Examples & Tutorials](examples.md) section.