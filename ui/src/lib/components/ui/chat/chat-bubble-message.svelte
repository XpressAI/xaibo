<!--
	Installed from github/ieedan/shadcn-svelte-extras
-->

<script lang="ts">
	import type { Snippet } from 'svelte';
	import LoadingDots from './loading-dots.svelte';
	import { cn } from '$lib/utils';

	type Props = {
		class?: string;
		typing?: boolean;
		children?: Snippet<[]>;
	};

	let { typing = false, class: className, children }: Props = $props();
</script>

<div
	class={cn(
		"order-2 rounded-lg bg-secondary p-4 text-sm group-data-[variant='sent']/chat-bubble:order-1 group-data-[variant='received']/chat-bubble:rounded-bl-none group-data-[variant='sent']/chat-bubble:rounded-br-none group-data-[variant='sent']/chat-bubble:bg-primary group-data-[variant='sent']/chat-bubble:text-primary-foreground",
		className
	)}
>
	{#if typing}
		<div class="flex size-full place-items-center justify-center">
			<LoadingDots />
		</div>
	{:else}
		{@render children?.()}
	{/if}
</div>
