<script lang="ts">
    import type { CallGroup } from "$lib/components/custom/event-sequence/types";
    import type { NodeType } from "$lib/components/custom/agent-config/types";

    type Props = {
        eventGroup: CallGroup,
        rects: {
            containerRect: DOMRect,
            lifelineRect: DOMRect,
            boxRect: DOMRect,
        }
        module: NodeType,
        onclick?: () => void
    }

    let {
        eventGroup = $bindable(), 
        module,
        rects,
        onclick
    }: Props = $props();
    let {containerRect, lifelineRect, boxRect} = $derived(rects);

    let top = $derived(boxRect.top - containerRect.y);
    let height = $derived(((eventGroup.length + 1) /2) * boxRect.height);
    
    let hasResponse = $derived(!!eventGroup.response || !!eventGroup.exception);
    let backgroundClass = $derived.by(() => {
        let base = " bg-gradient-to-b ";
        let gradient;
        if(!hasResponse) {
            gradient = getNodeGradientNoResponse(module);
        }else{
            gradient = getNodeGradient(module);
        }
        return base + `${gradient.from} ${gradient.to}`;
    });

    // Calculate positioning values in one go
    let coordinates = $derived.by(() => {
        if(lifelineRect && containerRect) {
            return {
                top: lifelineRect.top - containerRect.top,
                left: lifelineRect.left - containerRect.left
            };
        }else{
            return {top: 0, left: 0}
        }
    });

    function getNodeGradient(node: NodeType) {
		if (node.isEntry) return { from: 'from-green-300', to: 'to-green-400' }; // Green for entry
		if (node.id === '__response__') return { from: 'from-blue-300', to: 'to-blue-400' }; // Blue for response
		if (node.module.includes('LLM')) return { from: 'from-orange-300', to: 'to-orange-400' }; // Orange for LLM
		if (node.module.includes('Tool')) return { from: 'from-purple-300', to: 'to-purple-400' }; // Purple for tools
		if (node.module.includes('orchestrator')) return { from: 'from-red-300', to: 'to-red-400' }; // Red for orchestrator
		return { from: 'from-slate-300', to: 'to-slate-400' }; // Default gray
	}

    function getNodeGradientNoResponse(node: NodeType) {
		if (node.isEntry) return { from: 'from-green-600', to: 'to-green-50' }; // Green for entry
		if (node.id === '__response__') return { from: 'from-blue-600', to: 'to-blue-50' }; // Blue for response
		if (node.module.includes('LLM')) return { from: 'from-orange-600', to: 'to-orange-50' }; // Orange for LLM
		if (node.module.includes('Tool')) return { from: 'from-purple-600', to: 'to-purple-50' }; // Purple for tools
		if (node.module.includes('orchestrator')) return { from: 'from-red-600', to: 'to-red-50' }; // Red for orchestrator
		return { from: 'from-slate-600', to: 'to-slate-50' }; // Default gray
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div 
    bind:this={eventGroup.ref}
    {onclick}
    class="cursor-pointer absolute border w-6 rounded hover:scale-105 hover:shadow-lg transition-[box-shadow,transform] duration-300 {backgroundClass}"
    style="height: {height}px; left: calc({coordinates.left}px - 0.75rem); top: {top}px;">
</div>
