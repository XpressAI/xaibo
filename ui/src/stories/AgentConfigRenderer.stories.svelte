<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import AgentConfigRenderer from '$lib/components/custom/AgentConfigRenderer.svelte';

    const complexConfig = {
		id: 'complex-agent',
		modules: [
			{
				module: 'xaibo.primitives.modules.llm.OpenAILLM',
				id: 'llm',
				provides: ['LLMProtocol'],
				uses: null,
				config: { model: 'gpt-4' }
			},
			{
				module: 'xaibo.primitives.modules.tools.PythonToolProvider',
				id: 'simple-tools',
				provides: ['ToolProviderProtocol'],
				uses: null,
				config: { tool_packages: ['xaibo_examples.demo_tools.demo_tools'] }
			},
			{
				module: 'xaibo.primitives.modules.orchestrator.StressingToolUser',
				id: 'orchestrator',
				provides: ['TextMessageHandlerProtocol'],
				uses: ['ResponseProtocol', 'LLMProtocol', 'ToolProviderProtocol'],
				config: {
					max_thoughts: 10,
					system_prompt: 'You are a helpful assistant with access to a variety of tools.'
				}
			},
			{
				module: 'xaibo.primitives.modules.ResponseHandler',
				id: '__response__',
				provides: ['ResponseProtocol'],
				uses: null,
				config: null
			}
		],
		exchange: [
			{
				module: 'orchestrator',
				protocol: 'ResponseProtocol',
				provider: '__response__'
			},
			{
				module: 'orchestrator',
				protocol: 'LLMProtocol',
				provider: 'llm'
			},
			{
				module: 'orchestrator',
				protocol: 'ToolProviderProtocol',
				provider: 'simple-tools'
			},
			{
				module: '__entry__',
				protocol: 'TextMessageHandlerProtocol',
				provider: 'orchestrator'
			}
		]
	};

    const moreComplexConfig = {
        "id": "hodlbot",
        "modules": [{
            "module": "xaibo.primitives.modules.llm.OpenAILLM",
            "id": "llm",
            "provides": ["LLMProtocol"],
            "uses": null,
            "config": {"model": "gpt-4o-mini", "api_key": "not-a-real-key"}
        }, {
            "module": "xai_components.xai_xaibo.xaibo_components.XircuitsToolProvider",
            "id": "tools",
            "provides": ["ToolProviderProtocol"],
            "uses": null,
            "config": {
                "toolbelt_spec": {"get_current_time": ["get_current_time", "Returns the current time in ISO format. Doesn't take any parameters.", ["text"], ["text"]]},
                "force_single_param": false
            }
        }, {
            "module": "xaibo.primitives.modules.orchestrator.StressingToolUser",
            "id": "orchestrator",
            "provides": ["TextMessageHandlerProtocol"],
            "uses": ["ResponseProtocol", "LLMProtocol", "ToolProviderProtocol"],
            "config": {"max_thoughts": 5, "system_prompt": "You are a bot that helps people figure out time zones."}
        }, {
            "module": "xaibo.primitives.modules.tools.TextBasedToolCallAdapter",
            "id": "tool_adapter",
            "provides": ["LLMProtocol"],
            "uses": ["LLMProtocol"],
            "config": null
        }, {
            "module": "xaibo.primitives.modules.ResponseHandler",
            "id": "__response__",
            "provides": ["ResponseProtocol"],
            "uses": null,
            "config": null
        }],
        "exchange": [{
            "module": "tool_adapter",
            "protocol": "LLMProtocol",
            "provider": "llm"
        }, {"module": "orchestrator", "protocol": "LLMProtocol", "provider": "tool_adapter"}, {
            "module": "orchestrator",
            "protocol": "ResponseProtocol",
            "provider": "__response__"
        }, {"module": "orchestrator", "protocol": "ToolProviderProtocol", "provider": "tools"}, {
            "module": "__entry__",
            "protocol": "TextMessageHandlerProtocol",
            "provider": "orchestrator"
        }]
    }


	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'Custom/AgentConfigRenderer',
		component: AgentConfigRenderer,
		tags: ['autodocs'],
		argTypes: {
			config: {
				control: 'object',
				description: 'The agent configuration object to render'
			},
            dark: {
                control: 'boolean',
                description: 'switches darkmode on an off'
            }
		}
	});
</script>

<Story name="Complex Configuration" args={{ config: complexConfig }} />
<Story name="Complex Configuration (Dark)" args={{ config: complexConfig, dark: true }} />
<Story name="Other Complex Configuration" args={{ config: moreComplexConfig }} />

