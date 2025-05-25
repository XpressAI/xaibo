# How to switch between different LLM providers

This guide shows you how to configure your Xaibo agents to use different LLM providers like OpenAI, Anthropic, Google, or AWS Bedrock.

## Switch to OpenAI models

Install the OpenAI dependency and configure your agent:

```bash
pip install xaibo[openai]
```

```yaml
# agents/openai_agent.yml
id: openai-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}  # Optional, uses env var by default
      temperature: 0.7
      max_tokens: 2000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your API key:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

## Switch to Anthropic Claude

Install Anthropic dependencies and configure Claude:

```bash
pip install xaibo[anthropic]
```

```yaml
# agents/claude_agent.yml
id: claude-agent
modules:
  - module: xaibo.primitives.modules.llm.AnthropicLLM
    id: llm
    config:
      model: claude-3-5-sonnet-20241022
      api_key: ${ANTHROPIC_API_KEY}
      temperature: 0.7
      max_tokens: 4000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```


## Switch to Google Gemini

Install Google dependencies and configure Gemini:

```bash
pip install xaibo[google]
```

```yaml
# agents/gemini_agent.yml
id: gemini-agent
modules:
  - module: xaibo.primitives.modules.llm.GoogleLLM
    id: llm
    config:
      model: gemini-2.0-flash-001
      api_key: ${GOOGLE_API_KEY}
      temperature: 0.7
      max_tokens: 2000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your API key:

```bash
export GOOGLE_API_KEY=your_google_api_key_here
```

## Switch to AWS Bedrock

Install Bedrock dependencies and configure AWS models:

```bash
pip install xaibo[bedrock]
```

```yaml
# agents/bedrock_agent.yml
id: bedrock-agent
modules:
  - module: xaibo.primitives.modules.llm.BedrockLLM
    id: llm
    config:
      model: anthropic.claude-3-5-sonnet-20241022-v2:0
      region_name: us-east-1
      aws_access_key_id: ${AWS_ACCESS_KEY_ID}
      aws_secret_access_key: ${AWS_SECRET_ACCESS_KEY}
      temperature: 0.7
      max_tokens: 4000
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

Set your AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=your_aws_access_key
export AWS_SECRET_ACCESS_KEY=your_aws_secret_key
export AWS_DEFAULT_REGION=us-east-1
```


## Use custom API endpoints

Configure custom endpoints for OpenAI-compatible APIs:

```yaml
# agents/custom_openai_agent.yml
id: custom-openai-agent
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: your-custom-model
      base_url: https://your-custom-endpoint.com/v1
      api_key: ${CUSTOM_API_KEY}
      timeout: 120.0
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
```

This works with:

- Local LLM servers (Ollama, LM Studio)
- Azure OpenAI Service
- Custom OpenAI-compatible APIs


## Best practices

### Provider selection

- Choose based on your specific use case requirements
- Consider cost, performance, and feature needs
- Test multiple providers for critical applications

### Configuration management

- Use environment variables for API keys
- Store provider configs in separate files
- Version control your configurations

### Fallback strategies

- Configure backup providers for reliability
- Implement retry logic with exponential backoff
- Monitor provider availability and performance

### Security

- Rotate API keys regularly
- Use least-privilege access policies
- Monitor usage for anomalies

## Troubleshooting

### Authentication errors

- Verify API keys are correct and active
- Check account billing status and limits
- Ensure proper environment variable setup

### Model availability

- Verify model names match provider specifications
- Check regional availability for specific models
- Update to latest model versions when needed

### Rate limiting

- Implement proper retry logic with backoff
- Monitor usage against provider limits
- Consider upgrading to higher-tier plans

### Performance issues

- Adjust timeout values for slow responses
- Optimize prompt length and complexity
- Monitor token usage and costs