<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import EventSequenceRenderer from '$lib/components/custom/EventSequenceRenderer.svelte';

	import { EventType } from '$lib/components/custom/event-sequence/types';

    import {events, config} from './exampleData';

	const simpleConfig = {
		id: 'simple-agent',
		modules: [
			{
				module: 'xaibo.primitives.modules.llm.OpenAILLM',
				id: 'llm',
				provides: ['LLMProtocol'],
				uses: null,
				config: { model: 'gpt-4.1-nano' }
			},
			{
				module: 'xaibo.primitives.modules.orchestrator.StressingToolUser',
				id: 'orchestrator',
				provides: ['TextMessageHandlerProtocol'],
				uses: ['ResponseProtocol', 'LLMProtocol'],
				config: {
					max_thoughts: 3,
					system_prompt: 'You are a helpful assistant.'
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
				module: '__entry__',
				protocol: 'TextMessageHandlerProtocol',
				provider: 'orchestrator'
			}
		]
	};

	const simpleEvents = [
		{
			agent_id: 'simple-agent',
			event_name: 'handle_message',
			event_type: EventType.CALL,
			module_class: 'StressingToolUser',
			module_id: 'orchestrator',
			method_name: 'handle_message',
			time: 1000,
			call_id: '1',
			caller_id: 'agent:simple-agent',
			arguments: { message: 'Hello, how are you?' }
		},
		{
			agent_id: 'simple-agent',
			event_name: 'generate',
			event_type: EventType.CALL,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1100,
			call_id: '2',
			caller_id: 'orchestrator',
			arguments: { prompt: 'You are a helpful assistant. User: Hello, how are you?' }
		},
		{
			agent_id: 'simple-agent',
			event_name: 'generate',
			event_type: EventType.RESULT,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1300,
			call_id: '2',
			caller_id: 'orchestrator',
			result: 'I\'m doing well, thank you for asking! How can I assist you today?'
		},
		{
			agent_id: 'simple-agent',
			event_name: 'respond',
			event_type: EventType.CALL,
			module_class: 'ResponseHandler',
			module_id: '__response__',
			method_name: 'respond',
			time: 1400,
			call_id: '3',
			caller_id: 'orchestrator',
			arguments: { response: 'I\'m doing well, thank you for asking! How can I assist you today?' }
		},
		{
			agent_id: 'simple-agent',
			event_name: 'respond',
			event_type: EventType.RESULT,
			module_class: 'ResponseHandler',
			module_id: '__response__',
			method_name: 'respond',
			time: 1450,
			call_id: '3',
			caller_id: 'orchestrator',
			result: null
		},
		{
			agent_id: 'simple-agent',
			event_name: 'handle_message',
			event_type: EventType.RESULT,
			module_class: 'StressingToolUser',
			module_id: 'orchestrator',
			method_name: 'handle_message',
			time: 1500,
			call_id: '1',
			caller_id: 'agent:simple-agent',
			result: null
		}
	];

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

	const complexEvents = [
		{
			agent_id: 'complex-agent',
			event_name: 'handle_message',
			event_type: EventType.CALL,
			module_class: 'StressingToolUser',
			module_id: 'orchestrator',
			method_name: 'handle_message',
			time: 1000,
			call_id: '1',
			caller_id: 'agent:complex-agent',
			arguments: { message: 'What is the weather in New York?' }
		},
		{
			agent_id: 'complex-agent',
			event_name: 'generate',
			event_type: EventType.CALL,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1100,
			call_id: '2',
			caller_id: 'orchestrator',
			arguments: { prompt: 'You are a helpful assistant. User: What is the weather in New York?' }
		},
		{
			agent_id: 'complex-agent',
			event_name: 'generate',
			event_type: EventType.RESULT,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1300,
			call_id: '2',
			caller_id: 'orchestrator',
			result: 'I need to use the weather tool to check the current weather in New York.'
		},
		{
			agent_id: 'complex-agent',
			event_name: 'get_tools',
			event_type: EventType.CALL,
			module_class: 'PythonToolProvider',
			module_id: 'simple-tools',
			method_name: 'get_tools',
			time: 1400,
			call_id: '3',
			caller_id: 'orchestrator',
			arguments: {}
		},
		{
			agent_id: 'complex-agent',
			event_name: 'get_tools',
			event_type: EventType.RESULT,
			module_class: 'PythonToolProvider',
			module_id: 'simple-tools',
			method_name: 'get_tools',
			time: 1450,
			call_id: '3',
			caller_id: 'orchestrator',
			result: ['get_weather', 'get_time', 'search_web']
		},
		{
			agent_id: 'complex-agent',
			event_name: 'execute_tool',
			event_type: EventType.CALL,
			module_class: 'PythonToolProvider',
			module_id: 'simple-tools',
			method_name: 'execute_tool',
			time: 1500,
			call_id: '4',
			caller_id: 'orchestrator',
			arguments: { tool_name: 'get_weather', parameters: { city: 'New York' } }
		},
		{
			agent_id: 'complex-agent',
			event_name: 'execute_tool',
			event_type: EventType.RESULT,
			module_class: 'PythonToolProvider',
			module_id: 'simple-tools',
			method_name: 'execute_tool',
			time: 1600,
			call_id: '4',
			caller_id: 'orchestrator',
			result: { temperature: 72, conditions: 'Partly Cloudy', humidity: 65 }
		},
		{
			agent_id: 'complex-agent',
			event_name: 'generate',
			event_type: EventType.CALL,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1700,
			call_id: '5',
			caller_id: 'orchestrator',
			arguments: { prompt: 'You are a helpful assistant. User: What is the weather in New York?\nTool result: {"temperature": 72, "conditions": "Partly Cloudy", "humidity": 65}' }
		},
		{
			agent_id: 'complex-agent',
			event_name: 'generate',
			event_type: EventType.RESULT,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1800,
			call_id: '5',
			caller_id: 'orchestrator',
			result: 'The current weather in New York is partly cloudy with a temperature of 72°F and humidity at 65%.'
		},
		{
			agent_id: 'complex-agent',
			event_name: 'respond',
			event_type: EventType.CALL,
			module_class: 'ResponseHandler',
			module_id: '__response__',
			method_name: 'respond',
			time: 1900,
			call_id: '6',
			caller_id: 'orchestrator',
			arguments: { response: 'The current weather in New York is partly cloudy with a temperature of 72°F and humidity at 65%.' }
		},
		{
			agent_id: 'complex-agent',
			event_name: 'respond',
			event_type: EventType.RESULT,
			module_class: 'ResponseHandler',
			module_id: '__response__',
			method_name: 'respond',
			time: 1950,
			call_id: '6',
			caller_id: 'orchestrator',
			result: null
		},
		{
			agent_id: 'complex-agent',
			event_name: 'handle_message',
			event_type: EventType.RESULT,
			module_class: 'StressingToolUser',
			module_id: 'orchestrator',
			method_name: 'handle_message',
			time: 2000,
			call_id: '1',
			caller_id: 'agent:complex-agent',
			result: null
		}
	];

	const errorEvents = [
		...simpleEvents.slice(0, 2),
		{
			agent_id: 'simple-agent',
			event_name: 'generate',
			event_type: EventType.EXCEPTION,
			module_class: 'OpenAILLM',
			module_id: 'llm',
			method_name: 'generate',
			time: 1300,
			call_id: '2',
			caller_id: 'orchestrator',
			exception: 'API rate limit exceeded. Please try again later.'
		},
		{
			agent_id: 'simple-agent',
			event_name: 'handle_message',
			event_type: EventType.EXCEPTION,
			module_class: 'StressingToolUser',
			module_id: 'orchestrator',
			method_name: 'handle_message',
			time: 1400,
			call_id: '1',
			caller_id: 'agent:simple-agent',
			exception: 'Error in LLM generation: API rate limit exceeded'
		}
	];

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'Custom/EventSequenceRenderer',
		component: EventSequenceRenderer,
		tags: ['autodocs'],
		argTypes: {
			config: {
				control: 'object',
				description: 'The agent configuration object'
			},
			events: {
				control: 'object',
				description: 'The sequence of events to render'
			}
		},
		args: {
			config: simpleConfig,
			events: simpleEvents
		}
	});
</script>

<Story name="Simple Agent" />

<Story name="Complex Agent" args={{ config: complexConfig, events: complexEvents }} />

<Story name="Error Handling" args={{ config: simpleConfig, events: errorEvents }} />

<Story name="No Events" args={{ events: [] }} />

<Story name="Real Data" args={{ events, config }} />