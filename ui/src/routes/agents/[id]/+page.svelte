<script lang="ts">
	import PageHeader from "$lib/components/custom/PageHeader.svelte";
	import {page} from '$app/state';
    import EventSequenceRenderer from "$lib/components/custom/EventSequenceRenderer.svelte";

    let {data} = $props();
    let {AgentConfig, DebugTrace} = $derived(data);
    let {debugLog} = $derived($DebugTrace.data)
</script>

<PageHeader title={page.params.id} />
<div class="flex h-full w-full flex-col pr-4 pl-4 overflow-auto">
    <EventSequenceRenderer events={debugLog.events}/>
</div>


