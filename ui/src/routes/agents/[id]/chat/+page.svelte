<script lang="ts">
	import { page } from '$app/state';
	import PageHeader from "$lib/components/custom/PageHeader.svelte";
	import * as Chat from '$lib/components/ui/chat';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Button } from '$lib/components/ui/button';
	import Send from '@lucide/svelte/icons/send';
	import User from '@lucide/svelte/icons/user';
	import Bot from '@lucide/svelte/icons/bot';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import { tick, onMount } from 'svelte';

	type ChatMessage = {
		role: 'user' | 'assistant';
		content: string;
	};

	// Storage key based on agent ID for per-agent chat history
	const STORAGE_KEY = `chat-history-${page.params.id}`;

	let messages = $state<ChatMessage[]>([]);
	let inputMessage = $state('');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let chatContainerRef = $state<HTMLDivElement | null>(null);

	// Check if we're in the browser
	const isBrowser = typeof window !== 'undefined';

	// Load messages from sessionStorage on mount
	onMount(() => {
		if (!isBrowser) return;
		const stored = sessionStorage.getItem(STORAGE_KEY);
		if (stored) {
			try {
				messages = JSON.parse(stored);
			} catch (e) {
				console.error('Failed to load chat history:', e);
			}
		}
	});

	// Save messages to sessionStorage whenever they change
	$effect(() => {
		if (!isBrowser) return;
		if (messages.length > 0) {
			sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
		}
	});

	function clearChat() {
		if (confirm('Clear this conversation?')) {
			messages = [];
			sessionStorage.removeItem(STORAGE_KEY);
		}
	}

	async function sendMessage() {
		if (!inputMessage.trim() || isLoading) return;

		const userMessage = inputMessage.trim();
		inputMessage = '';
		errorMessage = '';
		isLoading = true;

		// Add user message to chat
		messages = [...messages, { role: 'user', content: userMessage }];

		// Scroll to bottom
		await tick();
		scrollToBottom();

		try {
			const response = await fetch(`/api/ui/chat/${page.params.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					message: userMessage,
					history: messages.slice(0, -1) // Exclude the message we just added
				})
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
				throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
			}

			const data = await response.json();

			// Add assistant response to chat
			messages = [...messages, { role: 'assistant', content: data.response }];
		} catch (error) {
			console.error('Error sending message:', error);
			errorMessage = error instanceof Error ? error.message : 'Failed to get response';
			// Remove the user message on error
			messages = messages.slice(0, -1);
		} finally {
			isLoading = false;
			await tick();
			scrollToBottom();
		}
	}

	function scrollToBottom() {
		if (chatContainerRef) {
			chatContainerRef.scrollTop = chatContainerRef.scrollHeight;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}
</script>

<div class="flex items-center justify-between mb-4 pr-4 pl-4">
	<PageHeader title="Chat with {page.params.id}" />
	{#if messages.length > 0}
		<Button variant="outline" size="sm" onclick={clearChat}>
			<Trash2 class="mr-2 h-4 w-4" />
			Clear Chat
		</Button>
	{/if}
</div>

<div class="flex h-[calc(100vh-10rem)] w-full flex-col pr-4 pl-4">
	<!-- Chat messages area -->
	<div class="flex-1 overflow-hidden rounded-lg border bg-card">
		<div bind:this={chatContainerRef} class="h-full overflow-y-auto">
			<Chat.List class="h-full">
				{#if messages.length === 0}
					<div class="flex h-full flex-col items-center justify-center text-muted-foreground">
						<Bot class="mb-4 h-12 w-12" />
						<p class="text-lg font-medium">Start a conversation</p>
						<p class="text-sm">Send a message to begin chatting with the agent</p>
					</div>
				{:else}
					{#each messages as message}
						<Chat.Bubble variant={message.role === 'user' ? 'sent' : 'received'}>
							<Chat.BubbleAvatar>
								{#if message.role === 'user'}
									<div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
										<User class="h-4 w-4 text-primary-foreground" />
									</div>
								{:else}
									<div class="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
										<Bot class="h-4 w-4 text-secondary-foreground" />
									</div>
								{/if}
							</Chat.BubbleAvatar>
							<Chat.BubbleMessage>
								{message.content}
							</Chat.BubbleMessage>
						</Chat.Bubble>
					{/each}
					{#if isLoading}
						<Chat.Bubble variant="received">
							<Chat.BubbleAvatar>
								<div class="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
									<Bot class="h-4 w-4 text-secondary-foreground" />
								</div>
							</Chat.BubbleAvatar>
							<Chat.BubbleMessage typing={true} />
						</Chat.Bubble>
					{/if}
				{/if}
			</Chat.List>
		</div>
	</div>

	<!-- Error message -->
	{#if errorMessage}
		<div class="mt-2 rounded-md bg-destructive/10 p-2 text-sm text-destructive">
			{errorMessage}
		</div>
	{/if}

	<!-- Input area -->
	<div class="mt-4 flex gap-2">
		<Textarea
			bind:value={inputMessage}
			placeholder="Type your message..."
			rows={2}
			class="flex-1 resize-none"
			onkeydown={handleKeydown}
			disabled={isLoading}
		/>
		<Button
			onclick={sendMessage}
			disabled={!inputMessage.trim() || isLoading}
			size="icon"
			class="shrink-0"
		>
			<Send class="h-4 w-4" />
		</Button>
	</div>
	<p class="mt-1 text-xs text-muted-foreground">Press Enter to send, Shift+Enter for new line</p>
</div>
