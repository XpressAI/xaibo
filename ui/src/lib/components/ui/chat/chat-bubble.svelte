<!--
	Installed from github/ieedan/shadcn-svelte-extras
-->

<script lang="ts">
	import type { Snippet } from 'svelte';

	type Props = {
		variant: 'sent' | 'received';
		children?: Snippet<[]>;
	};

	let { children, variant }: Props = $props();
</script>

<div
	class="group/chat-bubble flex max-w-[80%] flex-row place-items-end gap-2 data-[variant='sent']:place-self-end"
	data-variant={variant}
>
	{@render children?.()}
</div>
