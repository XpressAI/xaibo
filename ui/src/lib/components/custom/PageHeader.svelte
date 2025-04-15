<script lang="ts">
	type Props = {
		title: string;
		subtitle?: string;
	};
	let { title, subtitle }: Props = $props();
</script>

<div class="space-y-1">
	<h2 class="text-2xl font-semibold tracking-tight">
		{title}
	</h2>
	{#if subtitle}
		<p class="text-sm text-muted-foreground">
			{subtitle}
		</p>
	{/if}
</div>
