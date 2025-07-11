<script lang="ts">
	import { untrack } from 'svelte';
	import CircleOff from '@lucide/svelte/icons/circle-off';
	import type {LinkType, NodeType, Port} from "./agent-config/types"
	import Node from "./agent-config/node.svelte";
    import Link from "./agent-config/link.svelte";
	import {BoundingBox} from "$lib/components/reactivity";
	import {ScrollArea} from "$lib/components/ui/scroll-area";
	import type {AgentConfig$result} from "$houdini";
	import {SvelteMap} from "svelte/reactivity";

	type PropsType = {
		config: AgentConfig$result['agentConfig'];
		dark?: boolean;
		nodeClass?: string;
	}

	let { config, dark = false, nodeClass }: PropsType = $props();


	let container: HTMLDivElement | null = $state(null);
	let containerBB = $derived(new BoundingBox(container))

	let {nodes, links} = $derived.by(processConfig)
	let nodeRects = new SvelteMap<NodeType, {
		node: DOMRect,
		uses: DOMRect[],
		provides: DOMRect[]
	}>()

	function processConfig() {
		// Create nodes from modules
		let nodes: NodeType[] = [];
		let links:LinkType[] = [];
		nodes = config.modules.map(module => {
			return {
				id: module.id,
				module: module.module,
				provides: (module.provides || []).map((it: any) => ({ protocol: it, ref: null })),
				uses: (module.uses || []).map((it: any) => ({ protocol: it })),
				config: module.config,
				level: 0,
				isOpen: false
			};
		});

		// Add entry node if it's referenced in exchanges
		const hasEntryNode = config.exchange.some(
			(ex: any) => ex.module === '__entry__' || ex.provider === '__entry__'
		);
		if (hasEntryNode) {
			// Extract protocols used by the entry node from the exchange list
			const entryProvides = config.exchange
				.filter((ex: any) => ex.provider === '__entry__')
				.map((ex: any) => ({ protocol: ex.protocol as string, ref: null }));

			const entryUses = config.exchange
				.filter((ex: any) => ex.module === '__entry__')
				.map((ex: any) => ({ protocol: ex.protocol as string, ref: null }));

			nodes.push({
				id: '__entry__',
				module: 'Entry Point',
				provides: entryProvides,
				uses: entryUses,
				config: null,
				isEntry: true,
				level: 0,
				isOpen: false,
				ref: undefined
			});
		}

		// Sort provides and uses for each node based on the protocol matching the node module
		for (const node of nodes) {
			// Sort provides
			if (node.provides && node.provides.length > 0) {
				node.provides.sort((a, b) => {
					// Find nodes that use these protocols
					const aTargetNode = nodes.find(n => 
						n.uses && n.uses.some(use => use.protocol === a.protocol)
					);
					const bTargetNode = nodes.find(n => 
						n.uses && n.uses.some(use => use.protocol === b.protocol)
					);
					
					// Get the indices of these nodes
					const aIndex = aTargetNode ? nodes.indexOf(aTargetNode) : Infinity;
					const bIndex = bTargetNode ? nodes.indexOf(bTargetNode) : Infinity;
					
					return aIndex - bIndex;
				});
			}
			
			// Sort uses
			if (node.uses && node.uses.length > 0) {
				node.uses.sort((a, b) => {
					// Find the actual provider nodes from the exchange configuration
					const aExchange = config.exchange.find(ex =>
						ex.module === node.id && ex.protocol === a.protocol
					);
					const bExchange = config.exchange.find(ex => 
						ex.module === node.id && ex.protocol === b.protocol
					);
					
					// Find the actual source nodes based on the exchange
					const aSourceNode = aExchange ? nodes.find(n => n.id === aExchange.provider) : null;
					const bSourceNode = bExchange ? nodes.find(n => n.id === bExchange.provider) : null;
					
					// Get the indices of these nodes
					const aIndex = aSourceNode ? nodes.indexOf(aSourceNode) : Infinity;
					const bIndex = bSourceNode ? nodes.indexOf(bSourceNode) : Infinity;
					
					return aIndex - bIndex;
				});
			}
		}

		// Create links from exchange
		links = config.exchange.map((exchange, index: number) => {
			return {
				id: `link-${index}`,
				source: exchange.provider,
				sourcePort: exchange.protocol,
				target: exchange.module,
				targetPort: exchange.protocol,
				protocol: exchange.protocol
			};
		});

		// Apply hierarchical layout
		applyHierarchicalLayout(nodes, links);
		return {nodes, links};
	}

	function applyHierarchicalLayout(nodes: NodeType[], links: LinkType[]) {
		// Find entry points (nodes that are only providers, not consumers)
		// Entry nodes are those that don't consume anything (not targets of any link)
		const entryNodes = nodes.filter((node) => {
			return node.isEntry || !links.some((link) => link.target === node.id);
		});

		// Initialize all node levels to track maximum level reached
		const nodeLevels = new Map<string, number>();
		
		// Assign levels through BFS, following data flow from source to target
		const queue: { nodeId: string; level: number }[] = entryNodes.map((node) => ({
			nodeId: node.id,
			level: 0
		}));

		while (queue.length > 0) {
			const { nodeId, level } = queue.shift()!;

			// Update node level to maximum level reached (handles multiple paths)
			const currentLevel = nodeLevels.get(nodeId) || -1;
			if (level <= currentLevel) {
				continue; // Skip if we've already processed this node at a higher or equal level
			}
			
			nodeLevels.set(nodeId, level);

			// Find all nodes that this node provides to (outgoing links)
			const outgoingLinks = links.filter((link) => link.source === nodeId);
			for (const link of outgoingLinks) {
				const targetNode = nodes.find((n) => n.id === link.target);
				if (targetNode) {
					queue.push({ nodeId: targetNode.id, level: level + 1 });
				}
			}
		}

		// Apply the calculated levels to the nodes
		for (const node of nodes) {
			node.level = nodeLevels.get(node.id) || 0;
		}

		// Validation pass: ensure no target node has a lower level than its source
		let changed = true;
		while (changed) {
			changed = false;
			for (const link of links) {
				const sourceNode = nodes.find(n => n.id === link.target);
				const targetNode = nodes.find(n => n.id === link.source);
				
				if (sourceNode && targetNode) {
					const sourceLevel = sourceNode.level || 0;
					const targetLevel = targetNode.level || 0;
					const requiredTargetLevel = sourceLevel + 1;
					if (targetLevel < requiredTargetLevel) {
						targetNode.level = requiredTargetLevel;
						changed = true;
					}
				}
			}
		}

		// Post-processing step: reverse the level order
		// Find the maximum level
		let maxLevel = Math.max(...nodes.map(node => node.level || 0));
		
		// Reverse the levels so that the highest level becomes 0
		for (const node of nodes) {
			node.level = maxLevel - (node.level || 0);
		}

		maxLevel = Math.max(...nodes.map(node => node.level || 0));
		
		// Reverse the levels so that the highest level becomes 0
		for (const node of nodes) {
			node.level = maxLevel - (node.level || 0);
		}
	}

	function findPortIndexByProtocol(ports: Port[], protocol: string): number {
		return ports.findIndex((p) => p.protocol === protocol);
	}
</script>


<div class="w-full h-full flex" class:dark={dark}>
	<ScrollArea orientation="both" class="flex-1">
		<div class="relative">
			<!-- SVG for paths only -->
			<svg class="absolute inset-0" width="100%" height="100%">
				<!-- Links -->
				{#each links as link}
					{@const sourceNode = nodes.find(n => n.id === link.source)}
					{@const targetNode = nodes.find(n => n.id === link.target)}
					{@const sourcePortIdx = findPortIndexByProtocol(sourceNode?.provides || [], link.sourcePort)}
					{@const targetPortIdx = findPortIndexByProtocol(targetNode?.uses || [], link.targetPort)}

					{#if sourceNode && targetNode && sourcePortIdx >= 0 && targetPortIdx >= 0 && container}
						<Link
							id="path-{sourceNode.id}-{targetNode.id}"
							active={Math.random() < 0.33 ? "sending" : Math.random() < 0.5 ? "receiving" : null}
							rects={{
								container: containerBB.current,
								source: {
									port: nodeRects.get(sourceNode)?.provides[sourcePortIdx],
									node: nodeRects.get(sourceNode)?.node
								},
								target: {
									port: nodeRects.get(targetNode)?.uses[targetPortIdx],
									node: nodeRects.get(targetNode)?.node
								}
							}}
						/>
					{/if}
				{/each}
			</svg>

			<!-- Nodes organized by levels -->
			<div class="flex w-full flex-row justify-between overflow-visible" bind:this={container}>
				{#each [...new Set(nodes.map((n) => n.level))].toSorted() as level}
					<div class="flex flex-col justify-between">
						{#each nodes.filter((n) => n.level === level) as node (node)}
							<Node node={node} class={nodeClass} containerRect={containerBB.current} onPositionChange={(p) => nodeRects.set(node, p)}/>
						{/each}
					</div>
				{/each}
			</div>
		</div>

		{#if nodes.length === 0}
			<div class="flex flex-col items-center justify-center h-64 gap-4 text-gray-500 dark:text-gray-300">
				<CircleOff class="w-12 h-12" />
				<p class="text-sm font-medium">No configuration data available</p>
			</div>
		{/if}
	</ScrollArea>
</div>
