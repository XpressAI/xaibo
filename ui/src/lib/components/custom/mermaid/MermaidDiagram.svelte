<script lang="ts" module>
	import type { MermaidConfig, RenderResult } from 'mermaid';
	import mermaid from 'mermaid';

	const renderDiagram = async (
		config: MermaidConfig,
		code: string,
		id: string
	): Promise<RenderResult> => {
		// Should be able to call this multiple times without any issues.
		mermaid.initialize(config);
		return await mermaid.render(id, code);
	};

	const parse = async (code: string): Promise<unknown> => {
		return await mermaid.parse(code);
	};
</script>

<script lang="ts">
	let {
		def,
		config,
		id,
		onclick
	}: {
		config: MermaidConfig;
		def: string;
		id: string;
		onclick?: ((e: MouseEvent) => any) | undefined;
	} = $props();
	let rendered = $derived.by(async () => await renderDiagram(config, def, id));
</script>

{#await rendered then data}
	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
	<div class="diagram h-full w-full overflow-auto" {onclick}>
		{@html data.svg}
	</div>
{:catch error}
	<p class="text-red-500"><b>Error</b>:</p>
	<pre>{JSON.stringify(error, null, 4)}</pre>
{/await}
