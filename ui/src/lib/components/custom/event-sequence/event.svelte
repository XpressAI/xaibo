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
        const colors = [
            {from: 'from-green-400', to: 'to-green-300' },
            {from: 'from-blue-400', to: 'to-blue-300' },
            {from: 'from-orange-400', to: 'to-orange-300' },
            {from: 'from-purple-400', to: 'to-purple-300' },
            {from: 'from-red-400', to: 'to-red-300' },
            {from: 'from-slate-400', to: 'to-slate-300'}
        ];

        let hash = node.module.length;
        for (let i = 0; i < node.module.length; i++) {
            hash += node.module.charCodeAt(i);
        }
        return colors[hash % colors.length];
	}

    function getNodeGradientNoResponse(node: NodeType) {
        const colors = [
            {from: 'from-green-600', to: 'to-green-50' },
            {from: 'from-blue-600', to: 'to-blue-50' },
            {from: 'from-orange-600', to: 'to-orange-50' },
            {from: 'from-purple-600', to: 'to-purple-50' },
            {from: 'from-red-600', to: 'to-red-50' },
            {from: 'from-slate-600', to: 'to-slate-50'}
        ];

        let hash = node.module.length;
        for (let i = 0; i < node.module.length; i++) {
            hash += node.module.charCodeAt(i);
        }
        return colors[hash % colors.length];
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div 
    bind:this={eventGroup.ref}
    {onclick}
    class="cursor-pointer absolute border w-6 rounded hover:scale-105 hover:shadow-lg transition-[box-shadow,transform] duration-300 {backgroundClass}"
    style="height: {height}px; left: calc({coordinates.left}px - 0.75rem); top: {top}px;">
</div>
