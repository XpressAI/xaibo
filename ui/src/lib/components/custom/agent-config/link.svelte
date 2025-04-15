<script lang="ts">
    import type {NodeType, Port} from './types';
    import {BoundingBox} from "$lib/components/reactivity.js";
    type Props = {
        id: string;
        rects: {
            source: {
                node: DOMRect;
                port: DOMRect;
            },
            target: {
                node: DOMRect;
                port: DOMRect;
            },
            container: DOMRect;
        },

        active?: null | "receiving" | "sending";
    }
    let {id, rects, active = null}: Props = $props();

    let path = $derived.by(generatePath)

    function getPortPosition(
		rect: DOMRect,
		isInput: boolean,
	): { x: number; y: number } {
		if (!rect) return { x: 0, y: 0 };
		// Calculate position relative to the container
		const x = isInput ? rect.right - rects.container.left : rect.left - rects.container.left;
		const y = rect.top + rect.height / 2 - rects.container.top;

		return { x, y };
	}

	function generatePath(): string {
        // The position may change depending on the node position, so by mentioning
        // it here, we can depend on it.
        rects.container;
        rects.source.node;
        rects.target.node;

		const source = getPortPosition(rects.source.port, false);
		const target = getPortPosition(rects.target.port, true);

		// If we don't have valid positions yet, return an empty path
		if ((source.x === 0 && source.y === 0) || (target.x === 0 && target.y === 0)) {
			return '';
		}

		// Add a straight segment at the beginning (10px straight out)
		const straightSegmentLength = 5;
		const sourceExtendedX = source.x - straightSegmentLength;

		// Add a straight segment at the end (10px straight in)
		const targetExtendedX = target.x + straightSegmentLength;

		const dx = targetExtendedX - sourceExtendedX;
		const controlX = sourceExtendedX + dx / 2;

		return `M ${source.x} ${source.y} L ${sourceExtendedX} ${source.y} C ${controlX} ${source.y}, ${controlX} ${target.y}, ${targetExtendedX} ${target.y} L ${target.x} ${target.y}`;
	}
</script>

<g class="opacity-80">
    <path
        {id}
        d={path}
        class="fill-none stroke-gray-600 dark:stroke-gray-400 stroke-[2px] transition-colors duration-300 hover:stroke-blue-400 dark:hover:stroke-blue-500 hover:stroke-[3px]"
        class:active-path={active !== null}
    />
    
    {#if active === "receiving" || active === "sending"}
        {@const isReverse = active === "sending"}
        {@const pathId = `#${id}`}
        
        {#each [0, 0.3, 0.6] as delay, i}
            <circle r="3" fill="white" class="dot-animation" opacity={i === 0 ? 1 : i === 1 ? 0.7 : 0.4}>
                <animateMotion
                    dur="1.5s"
                    repeatCount="indefinite"
                    rotate="auto"
                    begin={delay ? `${delay}s` : undefined}
                    keyPoints={isReverse ? "1;0" : undefined}
                    keyTimes={isReverse ? "0;1" : undefined}
                    calcMode={isReverse ? "linear" : undefined}
                >
                    <mpath href={pathId} />
                </animateMotion>
            </circle>
        {/each}
    {/if}
</g>

<style>
    .active-path {
        stroke: #3b82f6 !important; /* blue-500 */
        stroke-width: 3px !important;
    }
    
    .dot-animation {
        filter: drop-shadow(0 0 2px rgba(59, 130, 246, 0.8));
    }
    
    :global(.dark) .dot-animation {
        fill: #93c5fd; /* blue-300 */
    }
</style>