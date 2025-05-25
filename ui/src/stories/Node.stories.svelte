<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import Node from '$lib/components/custom/agent-config/node.svelte';
	import type { NodeType } from '$lib/components/custom/agent-config/types';

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'Custom/Node',
		component: Node,
		tags: ['autodocs'],
		argTypes: {
			displayPorts: {
				control: 'boolean',
				description: 'Whether to display the input and output ports'
			}
		},
		args: {
			node: defaultNode(),
			displayPorts: true
		}
	});

	function defaultNode(): NodeType {
		return {
			ref: null,
			id: 'example-node',
			module: 'xaibo.example.Module',
			provides: [
				{ protocol: 'ExampleProtocol', ref: null },
				{ protocol: 'AnotherProtocol', ref: null }
			],
			uses: [
				{ protocol: 'InputProtocol', ref: null }
			],
			config: {
				param1: 'value1',
				param2: 42,
				nested: {
					key: 'value'
				}
			},
			level: 0,
			isOpen: false
		};
	}

	function llmNode(): NodeType {
		return {
			ref: null,
			id: 'llm',
			module: 'xaibo.primitives.modules.llm.OpenAILLM',
			provides: [
				{ protocol: 'LLMProtocol', ref: null }
			],
			uses: [],
			config: { 
				model: 'gpt-4.1-nano',
				temperature: 0.7,
				max_tokens: 1000
			},
			level: 1,
			isOpen: false
		};
	}

	function toolNode(): NodeType {
		return {
			ref: null,
			id: 'simple-tools',
			module: 'xaibo.primitives.modules.tools.PythonToolProvider',
			provides: [
				{ protocol: 'ToolProviderProtocol', ref: null }
			],
			uses: [],
			config: { 
				tool_packages: ['xaibo_examples.demo_tools.demo_tools'] 
			},
			level: 1,
			isOpen: false
		};
	}

	function orchestratorNode(): NodeType {
		return {
			ref: null,
			id: 'orchestrator',
			module: 'xaibo.primitives.modules.orchestrator.StressingToolUser',
			provides: [
				{ protocol: 'TextMessageHandlerProtocol', ref: null }
			],
			uses: [
				{ protocol: 'ResponseProtocol', ref: null },
				{ protocol: 'LLMProtocol', ref: null },
				{ protocol: 'ToolProviderProtocol', ref: null }
			],
			config: {
				max_thoughts: 10,
				system_prompt: 'You are a helpful assistant with access to a variety of tools.'
			},
			level: 0,
			isOpen: false
		};
	}

	function entryNode(): NodeType {
		return {
			ref: null,
			id: '__entry__',
			module: 'Entry Point',
			provides: [],
			uses: [
				{ protocol: 'TextMessageHandlerProtocol', ref: null }
			],
			config: null,
			isEntry: true,
			level: 0,
			isOpen: false
		};
	}

	function responseNode(): NodeType {
		return {
			ref: null,
			id: '__response__',
			module: 'xaibo.primitives.modules.ResponseHandler',
			provides: [
				{ protocol: 'ResponseProtocol', ref: null }
			],
			uses: [],
			config: null,
			level: 2,
			isOpen: false
		};
	}
</script>

<Story name="Default" />

<Story name="LLM Node" args={{ node: llmNode() }} />

<Story name="Tool Node" args={{ node: toolNode() }} />

<Story name="Orchestrator Node" args={{ node: orchestratorNode() }} />

<Story name="Entry Node" args={{ node: entryNode() }} />

<Story name="Response Node" args={{ node: responseNode() }} />

<Story name="Expanded Node" args={{ node: { ...defaultNode(), isOpen: true } }} />

<Story name="Without Ports" args={{ displayPorts: false }} />
