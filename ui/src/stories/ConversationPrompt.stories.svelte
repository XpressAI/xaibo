<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import ConversationPrompt from '$lib/components/custom/ConversationPrompt.svelte';
	import { fn } from '@storybook/test';

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'Custom/ConversationPrompt',
		component: ConversationPrompt,
		tags: ['autodocs'],
		args: {
			systemPrompt: '',
			messages: [],
			onchange: fn()
		}
	});
</script>

<Story 
	name="Empty" 
/>

<Story 
	name="With System Prompt" 
	args={{ 
		systemPrompt: "You are a helpful AI assistant that specializes in JavaScript programming." 
	}} 
/>

<Story 
	name="With Messages" 
	args={{ 
		systemPrompt: "You are a helpful AI assistant that specializes in JavaScript programming.",
		messages: [
			{ role: 'user', content: 'How do I create a Promise in JavaScript?' },
			{ role: 'assistant', content: 'To create a Promise in JavaScript, you can use the Promise constructor like this:\n\n```javascript\nconst myPromise = new Promise((resolve, reject) => {\n  // Asynchronous operation here\n  if (/* operation successful */) {\n    resolve(result);\n  } else {\n    reject(error);\n  }\n});\n```\n\nYou can then use `.then()` and `.catch()` to handle the resolved value or errors.' }
		]
	}} 
/>

<Story 
	name="Multiple Conversation Turns" 
	args={{ 
		systemPrompt: "You are a helpful AI assistant that specializes in JavaScript programming.",
		messages: [
			{ role: 'user', content: 'How do I create a Promise in JavaScript?' },
			{ role: 'assistant', content: 'To create a Promise in JavaScript, you can use the Promise constructor like this:\n\n```javascript\nconst myPromise = new Promise((resolve, reject) => {\n  // Asynchronous operation here\n  if (/* operation successful */) {\n    resolve(result);\n  } else {\n    reject(error);\n  }\n});\n```\n\nYou can then use `.then()` and `.catch()` to handle the resolved value or errors.' },
			{ role: 'user', content: 'What about async/await?' },
			{ role: 'assistant', content: 'Async/await is a more modern and cleaner way to work with Promises in JavaScript.\n\n```javascript\nasync function myAsyncFunction() {\n  try {\n    const result = await somePromiseReturningFunction();\n    console.log(result);\n  } catch (error) {\n    console.error(error);\n  }\n}\n```\n\nThe `async` keyword before a function makes it return a Promise automatically, and the `await` keyword can only be used inside async functions to wait for a Promise to resolve.' }
		]
	}} 
/>

<Story 
	name="Empty Messages Array" 
	args={{ 
		systemPrompt: "You are a helpful AI assistant.",
		messages: []
	}} 
/>
