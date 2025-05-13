<script lang="ts">
	import type { NodeType } from './types';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import ChevronUp from '@lucide/svelte/icons/chevron-up';
    import {ScrollArea} from '$lib/components/ui/scroll-area';
	import {untrack} from "svelte";
	import {BoundingBox} from "$lib/components/reactivity";

	type Props = {
		node: NodeType;
        displayPorts?: boolean;
		class?: string;
		containerRect?: DOMRect;
		onPositionChange?: (positions: {
			node: DOMRect,
			uses: DOMRect[],
			provides: DOMRect[]
		}) => void
	};

	let {
		node,
		displayPorts = true,
		class: className,
		containerRect,
		onPositionChange,
	}: Props = $props();

	let isOpen = $state(false);

	function toggleExpand() {
		isOpen = !isOpen;
	}

	function getNodeColor(node: NodeType) {
		const colors = ['bg-green-500', 'bg-blue-500', 'bg-orange-500', 'bg-purple-500', 'bg-red-500', 'bg-slate-500'];

		let hash = node.module.length;
		for (let i = 0; i < node.module.length; i++) {
			hash += node.module.charCodeAt(i);
		}
		return colors[hash % colors.length];
	}

	function getNodeGradient(node: NodeType) {
		const colors = [
			{from: 'from-green-600', to: 'to-green-400' },
			{from: 'from-blue-600', to: 'to-blue-400' },
			{from: 'from-orange-600', to: 'to-orange-400' },
			{from: 'from-purple-600', to: 'to-purple-400' },
			{from: 'from-red-600', to: 'to-red-400' },
			{from: 'from-slate-600', to: 'to-slate-400'}
		];

		let hash = node.module.length;
		for (let i = 0; i < node.module.length; i++) {
			hash += node.module.charCodeAt(i);
		}
		return colors[hash % colors.length];
	}

	function getNodeLabel(node: NodeType) {
		const parts = node.module.split('.');
		return parts[parts.length - 1] || node.id;
	}

	let nodeRef = $state<HTMLElement>();
	let usesRefs = $state<HTMLElement[]>([]);
	let providesRefs = $state<HTMLElement[]>([]);

	let nodeBbox = $derived(new BoundingBox(nodeRef));
	let usesBoxes = $derived(usesRefs.map(r => new BoundingBox(r)));
	let providesBoxes = $derived(providesRefs.map(r => new BoundingBox(r)));
	let positions = $derived({
			container: containerRect,
			node: nodeBbox.current,
			uses: usesBoxes.map(r => r.current),
			provides: providesBoxes.map(r => r.current),
	});
	$effect(() => {
		if(onPositionChange){
			onPositionChange(positions);
		}
	})
</script>

<div bind:this={nodeRef}
	class="{getNodeColor(node)} {className} m-4 max-w-fit overflow-visible rounded-lg border border-gray-300 dark:border-gray-700 shadow-lg transform text-black/80 dark:text-white transition-all duration-200 hover:shadow-2xl"
>
	<div class="rounded-t-lg bg-white/20 dark:bg-black/20 px-2 py-1">
		<div class="flex items-center justify-between">
			<div class="flex items-center truncate text-sm font-bold">
				{node.id}
			</div>
			{#if node.config && displayPorts}
				<button 
					class="p-1 rounded-full hover:bg-white/20 dark:hover:bg-black/20 transition-colors"
					onclick={toggleExpand}
					aria-label={node.isOpen ? "Collapse node" : "Expand node"}
                    title="Show Module Config"
				>
					{#if node.isOpen}
						<ChevronUp class="size-4" />
					{:else}
						<ChevronDown class="size-4" />
					{/if}
				</button>
			{/if}
		</div>
		<div class="truncate text-xs dark:text-white font-extralight">{getNodeLabel(node)}</div>
	</div>

    {#if displayPorts}
	<div class="bg-white/80 dark:bg-black/90 p-1 px-3 gap-2 flex flex-col border-t border-gray-200 dark:border-gray-700">
		<!-- Output ports (provides) -->
		{#if node.provides && node.provides.length > 0}
			<div>
				<div class="flex flex-col gap-1">
					{#each node.provides as port, i}
						<div class="group relative flex items-center text-xs">
							<div
								bind:this={providesRefs[i]}
								class="h-2 w-2 rounded-full border border-gray-400 dark:border-gray-500 {getNodeColor(
									node
								)} absolute -left-4 transition-colors group-hover:bg-black/50"
							></div>
							<div class="flex-1 truncate cursor-default">
								{port.protocol}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Input ports (uses) -->
		{#if node.uses && node.uses.length > 0}
			<div>
				<div class="flex flex-col gap-1">
					{#each node.uses as port, i}
						<div class="group relative flex items-center justify-between text-xs">
							<div class="flex-1 truncate text-right cursor-default">
								{port.protocol}
							</div>
							<div
								bind:this={usesRefs[i]}
								class="h-2 w-2 rounded-full border border-gray-400 dark:border-gray-500 {getNodeColor(
									node
								)} absolute -right-4 transition-colors group-hover:bg-black/50"
							></div>
						</div>
					{/each}
				</div>
			</div>
		{/if}


		<!-- Config section (expandable) -->
		{#if isOpen && node.config}
            <div class="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                <div class="text-xs font-semibold mb-1">Configuration:</div>
                <ScrollArea class="max-w-96" orientation="both">
                    <pre class="text-xs bg-gray-50 dark:bg-gray-700 p-2 rounded">{JSON.stringify(node.config, null, 2)}</pre>
                </ScrollArea>
            </div>
		{/if}
	</div>
    {/if}
	<div
		class="h-1 rounded-b bg-gradient-to-r
        {getNodeGradient(node).from} 
        {getNodeGradient(node).to}"
	></div>
</div>
