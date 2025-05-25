<script lang="ts">
    import {untrack} from 'svelte';
    import type {CallGroup, Event} from './event-sequence/types';
    import {EventType} from './event-sequence/types';
    import Node from './agent-config/node.svelte';
    import {ScrollArea} from '$lib/components/ui/scroll-area';
    import ArrowRight from '@lucide/svelte/icons/arrow-right';
    import AlertCircle from '@lucide/svelte/icons/alert-circle';
    import CheckCircle from '@lucide/svelte/icons/check-circle';
    import X from '@lucide/svelte/icons/x';
    import Maximize_2 from '@lucide/svelte/icons/maximize-2';
    import EventNode from './event-sequence/event.svelte';
    import EventLink from './event-sequence/event-link.svelte';
    import {BoundingBox} from "$lib/components/reactivity";
    import * as Breadcrumb from '$lib/components/ui/breadcrumb';
    import {Button} from "$lib/components/ui/button";
    import { JSONEditor, Mode } from 'svelte-jsoneditor'
    import * as Dialog from "$lib/components/ui/dialog";


    let {events = $bindable([])} = $props<{
        events: Event[];
    }>();

    interface NodeType {
        id: string;
        module: string;
        isEntry: boolean;
    }

    // State variables
    let nodes = $state<NodeType[]>([]);
    let nodesById = $state<Record<string, NodeType>>({});
    let eventGroups = $state<CallGroup[]>([]);

    // Process config when it changes
    $effect(() => {
        if (events) {
            untrack(() => processConfig());
        }
        if (events.length > 0) {
            untrack(() => processEvents());
        }
    });

    // Configuration processing
    function processConfig() {
        // Create nodes from modules in event log
        nodesById = {};
        events.forEach(event => {
            nodesById[event.module_id] = {
                id: event.module_id,
                module: event.module_class,
                isEntry: event.module_id == '__entry__'
            }
        })
        nodes = Object.values(nodesById)

        // Add entry node if referenced in exchanges
        //addEntryNodeIfNeeded();

        // Sort nodes based on first appearance in events
        if (events.length > 0) {
            const nodeOrder = new Map<string, number>();

            // Map each node ID to its first appearance index
            for (let i = 0; i < events.length; i++) {
                const event = events[i];
                if (!nodeOrder.has(event.caller_id)) {
                    nodeOrder.set(event.caller_id, i);
                }
                if (!nodeOrder.has(event.module_id)) {
                    nodeOrder.set(event.module_id, i + 1);
                }
            }

            // Sort nodes array based on first appearance index
            nodes.sort((a, b) => {
                const indexA = nodeOrder.get(a.id) ?? Infinity;
                const indexB = nodeOrder.get(b.id) ?? Infinity;
                return indexA - indexB;
            });
        }
    }

    function addEntryNodeIfNeeded() {
        const hasEntryNode = !!nodesById['__entry__'] || config.exchange.some(
            (ex: any) => ex.module === '__entry__' || ex.provider === '__entry__'
        );

        if (hasEntryNode) {
            const entryProvides = config.exchange
                .filter((ex: any) => ex.provider === '__entry__')
                .map((ex: any) => ({protocol: ex.protocol as string, ref: null}));

            const entryUses = config.exchange
                .filter((ex: any) => ex.module === '__entry__')
                .map((ex: any) => ({protocol: ex.protocol as string, ref: null}));

            nodes.push({
                id: `__entry__`,
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
    }

    // Event processing
    function processEvents() {
        let groups = [] as CallGroup[];
        let openGroups: Map<string, CallGroup> = new Map();
        let callstack = [] as CallGroup[];
        // Add an additional event group that spans the entire sequence for the __entry__ module
        /*if (events.length > 0) {
            const entryGroup: CallGroup = {
                call: {
                    ...events[0],  // Copy properties from first event
                    module_id: `__entry__`,
                    module_class: "Entry Point",
                    call_id: "__entry__",
                    event_type: EventType.CALL
                },
                response: undefined,
                exception: undefined,
                parent: undefined,
                start: 0,
                length: events.length + 1  // Span the entire sequence
            };
            callstack.push(entryGroup);
            groups.push(entryGroup);

        }*/

        for (let i = 0; i < events.length; i++) {
            let event = events[i];
            let group: CallGroup;
            if (openGroups.has(event.call_id)) {
                group = openGroups.get(event.call_id)!;
                group.length = i - group.length;
                switch (event.event_type) {
                    case EventType.RESULT:
                        group.response = event;
                        break;
                    case EventType.EXCEPTION:
                        group.exception = event;
                        break;
                    default:
                        console.warn(`Trying to continue a call group with unsupported event: ${event.event_type} (call_id: ${event.call_id})`);
                        break;
                }
                if (callstack.length == 0) {
                    console.warn(`Closing out an event group that wasn't on the call stack: ${event.call_id}`);
                }

                const position = callstack.indexOf(group);
                if (position !== callstack.length - 1) {
                    console.warn(`Improper order of events. Closing out event group ${event.call_id} but it is not at the top of the stack (index ${position})`);
                }

                callstack.splice(position, 1);
                groups.push(group);
                openGroups.delete(event.call_id);
            } else {
                if (event.event_type != EventType.CALL) {
                    console.warn(`Starting off call group with something that is not a CALL event: ${event.event_type}`);
                    continue;
                }

                group = {
                    call: event,
                    response: undefined,
                    exception: undefined,
                    parent: callstack.length > 0 ? callstack[callstack.length - 1] : undefined,
                    length: i,
                    start: i
                }
                callstack.push(group);
                openGroups.set(event.call_id, group);
            }
        }
        eventGroups = groups.toSorted((a, b) => a.start - b.start);
    }

    let length = $derived(eventGroups.filter(it => it.parent === undefined).reduce((acc, cur) => acc + cur.length, 0))

    let container = $state<HTMLElement | null>(null);
    let lifelineRefs = $state<Record<string, HTMLDivElement>>({});
    let containerBB = $derived(new BoundingBox(container))
    // Create a derived record of DOMRects for each lifeline reference
    let lifelineBBs = $derived.by(() => {
        const rects: Record<string, BoundingBox> = {};

        for (const [id, ref] of Object.entries(lifelineRefs)) {
            if (ref) {
                rects[id] = new BoundingBox(ref);
            }
        }
        return rects;
    });

    // Create a derived record of DOMRects for each event box reference
    let eventBoxBBs = $derived(eventGroups.map(group => new BoundingBox(group.ref)))
    let eventListBBs = $derived(eventGroups.map(group => new BoundingBox(group.boxRef)))

    function getNodeColor(node: NodeType) {
        const colors = ['bg-green-500', 'bg-blue-500', 'bg-orange-500', 'bg-purple-500', 'bg-red-500', 'bg-slate-500'];

        let hash = node.module.length;
        for (let i = 0; i < node.module.length; i++) {
            hash += node.module.charCodeAt(i);
        }
        return colors[hash % colors.length];
    }

    function getParentChain(group: CallGroup): NodeType[] {
        const result = [];
        let parent: CallGroup | undefined = group;
        while (parent) {
            result.push(nodesById[parent.call.module_id]);
            parent = parent.parent;
        }
        return result;
    }

    function getParentCallChain(group: CallGroup): CallGroup[] {
        const result = [];
        let parent: CallGroup | undefined = group.parent;
        while (parent) {
            result.push(parent);
            parent = parent.parent;
        }
        return result;
    }

    let selectedEventIdx = $state<number | undefined>(undefined);

    let fullScreenDetails: any = $state(null);
    $inspect(fullScreenDetails);
</script>

<div class="w-full h-full flex flex-col">
    <div class="text-lg font-semibold mb-2">Event Sequence</div>

    {#if events.length === 0}
        <div class="flex items-center justify-center h-full text-gray-500">
            No events to display
        </div>
    {:else}
        <div class="overflow-hidden flex">
            <div class="h-full overflow-auto {selectedEventIdx !== undefined? 'block w-fit' :'grid w-full grid-cols-[auto_1fr]'} relative">
                <div class="flex flex-col gap-0 border-r border-gray-200 dark:border-gray-700 pr-2">
                    <div class="h-24 bg-white"></div>
                    {#each eventGroups as group, i (i)}
                        {@const node = nodesById[group.call.module_id]}
                        {@const parentChain = getParentChain(group)}
                        {@const endEvent = (group.response || group.exception)}
                        <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
                        <div class="flex gap-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors items-center"
                             bind:this={group.boxRef}
                             class:bg-muted={selectedEventIdx === i}
                             onclick={() => selectedEventIdx = i}
                        >
                            <div class="flex flex-col flex-1 py-2 pl-2">
                                <div class="text-sm font-medium">{group.call.method_name}</div>
                                <div class="truncate text-xs text-gray-600 dark:text-gray-300 flex justify-between gap-2">
                                    {node.module.split('.').findLast(it => true)}
                                    <div class="text-gray-400 dark:text-gray-500">
                                        {#if endEvent}
                                            {((endEvent.time - group.call.time) * 1000).toFixed(2)}ms
                                        {/if}
                                    </div>
                                </div>
                            </div>
                            {#if group.exception}
                                <div class="text-red-500 self-center" title="Exception occurred">
                                    <AlertCircle size={16}/>
                                </div>
                            {/if}
                            <div class="flex h-full -mt-2 -mb-2">
                                {#each parentChain as node}
                                    {@const color = getNodeColor(node)}
                                    <div class={color} style="width: 5px; height: 52px"></div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                    <div class="h-4 bg-white"></div>
                </div>
                {#if selectedEventIdx === undefined}
                    <ScrollArea class="pb-2" orientation="horizontal">
                        <div class="relative">
                            <div class="flex flex-1" bind:this={container}>
                                {#each nodes as node, i (i)}
                                    <div class="flex flex-col items-center gap-2">
                                        <div class="sticky top-0 bg-white dark:bg-gray-800 z-[100]">
                                            <Node node={nodes[i]} displayPorts={false}/>
                                        </div>
                                        <div bind:this={lifelineRefs[node.id]} class="bg-gray-300 dark:bg-gray-600 w-px"
                                             style="height: {eventListBBs[eventGroups.length - 1].current.y - containerBB.current.y}px"></div>
                                    </div>
                                {/each}
                            </div>
                            <svg class="absolute inset-0" width="100%" height="100%">
                                <defs>
                                    <marker id="arrowhead-call" markerWidth="6" markerHeight="4" refX="5" refY="2"
                                            orient="auto">
                                        <polygon points="0 0, 6 2, 0 4" class="fill-gray-500 dark:fill-gray-400"/>
                                    </marker>
                                    <marker id="arrowhead-response-exception" markerWidth="6" markerHeight="4" refX="5"
                                            refY="2" orient="auto">
                                        <polygon points="0 0, 6 2, 0 4" class="fill-red-400 dark:fill-red-600"/>
                                    </marker>
                                    <marker id="arrowhead-response-result" markerWidth="6" markerHeight="4" refX="5"
                                            refY="2" orient="auto">
                                        <polygon points="0 0, 6 2, 0 4" class="fill-gray-500 dark:fill-gray-400"/>
                                    </marker>
                                </defs>
                                {#each eventGroups as eventGroup, i (i)}
                                    {#if i > 0}
                                        <EventLink {eventGroup}
                                                   rects={{
													   containerRect: containerBB.current,
													   lifelineRect: lifelineBBs[eventGroup.call.caller_id]?.current,
													   eventBoxRect: eventBoxBBs[i].current,
												   }}
                                        />
                                    {/if}
                                {/each}
                            </svg>
                            <div class="absolute inset-0 z-[99]">
                                {#each eventGroups as group, i (i)}
                                    <EventNode bind:eventGroup={eventGroups[i]}
                                               module={nodes.find(it => it.id === group.call.module_id)}
                                               onclick={() => selectedEventIdx = eventGroups.indexOf(group)}
                                               rects={{
														containerRect: containerBB.current,
														lifelineRect: lifelineBBs[group.call.module_id]?.current,
														boxRect: eventListBBs[i].current,
												  }}
                                    />
                                {/each}
                            </div>
                        </div>
                    </ScrollArea>
                {/if}
            </div>
            {#if selectedEventIdx !== undefined}
                {@const selectedEvent = eventGroups[selectedEventIdx]}
                {@const parentChain = getParentCallChain(selectedEvent)}
                <div class="p-4 @container flex-1 overflow-auto" >
                    <div class="flex flex-col gap-4">
                        <div class="flex flex-col">
                            <div class="flex justify-between items-center">
                                <h3 class="text-lg font-semibold">
                                    {selectedEvent.call.module_class}.{selectedEvent.call.method_name}
                                </h3>
                                <Button
                                        variant="ghost"
                                        size="icon"
                                        onclick={() => selectedEventIdx = undefined}
                                        class="h-8 w-8"
                                        title="Close details"
                                >
                                    <X size={16}/>
                                </Button>
                            </div>
                            <div class="mb-2">
                                <Breadcrumb.Root>
                                    <Breadcrumb.List>
                                        {#each parentChain.toReversed() as group, i}
                                            {#if i < parentChain.length - 1}
                                                <Breadcrumb.Item>
                                                    <Breadcrumb.Link class="text-xs cursor-pointer"
                                                                     onclick={() => selectedEventIdx = eventGroups.findIndex(g => g.call.call_id === group.call.call_id)}>
                                                        {group.call.module_class}.{group.call.method_name}
                                                    </Breadcrumb.Link>
                                                </Breadcrumb.Item>
                                                <Breadcrumb.Separator/>
                                            {:else}
                                                <Breadcrumb.Item>
                                                    <Breadcrumb.Page class="text-xs cursor-pointer"
                                                                     onclick={() => selectedEventIdx = eventGroups.findIndex(g => g.call.call_id === group.call.call_id)}>
                                                        {group.call.module_class}.{group.call.method_name}
                                                    </Breadcrumb.Page>
                                                </Breadcrumb.Item>
                                            {/if}
                                        {/each}
                                    </Breadcrumb.List>
                                </Breadcrumb.Root>
                            </div>
                            <div class="flex items-center gap-2">
                                {#if selectedEvent.exception}
                                    <div class="flex items-center gap-1 text-red-500">
                                        <AlertCircle size={16}/>
                                        <span>Exception</span>
                                    </div>
                                {:else if selectedEvent.response}
                                    <div class="flex items-center gap-1 text-green-500">
                                        <CheckCircle size={16}/>
                                        <span>Success</span>
                                    </div>
                                {/if}
                                {#if selectedEvent.response || selectedEvent.exception}
                                    <div class="text-sm text-gray-500">
                                        {((selectedEvent.response?.time || selectedEvent.exception?.time || 0) - selectedEvent.call.time) * 1000}
                                        ms
                                    </div>
                                {/if}
                            </div>
                        </div>

                        <div class="grid grid-cols-1 @md:grid-cols-2 gap-4">
                            <div class="flex flex-col gap-2">
                                <h4 class="font-medium">Call Details</h4>
                                <div class="flex-1 border rounded-md p-3 bg-gray-50 dark:bg-gray-800 overflow-auto">
                                    <div class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
                                        <span class="text-sm font-medium">Module:</span>
                                        <span class="text-sm">{nodesById[selectedEvent.call.module_id]?.module.split('.').findLast(it => true)}
                                            ({selectedEvent.call.module_id})</span>

                                        <span class="text-sm font-medium">Caller:</span>
                                        <span class="text-sm">{(nodesById[selectedEvent.call.caller_id]?.module || selectedEvent.call.caller_id).split('.').findLast(it => true)}
                                            ({selectedEvent.call.caller_id})</span>

                                        <span class="text-sm font-medium">Time:</span>
                                        <span class="text-sm">{new Date(selectedEvent.call.time * 1000).toISOString()}</span>

                                        <span class="text-sm font-medium">Call ID:</span>
                                        <span class="text-sm truncate">{selectedEvent.call.call_id}</span>
                                    </div>
                                </div>
                            </div>

                            {#if selectedEvent.call.arguments}
                                <div class="flex flex-col gap-2">
                                    <div class="flex gap-2 items-center">
                                        <h4 class="font-medium">Arguments</h4>
                                        <Button onclick={() => fullScreenDetails = selectedEvent.call.arguments} variant="ghost" size="icon">
                                            <Maximize_2 />
                                        </Button>
                                    </div>
                                    <div class="flex-1 overflow-auto max-h-[30vh]">
                                        <JSONEditor mode={Mode.text} content={{text: undefined, json: selectedEvent.call.arguments}} readOnly navigationBar={false}/>
                                    </div>
                                </div>
                            {/if}
                        </div>

                        {#if selectedEvent.response || selectedEvent.exception}
                            <div class="grid grid-cols-1 gap-4s">
                                {#if selectedEvent.response}
                                    <div class="flex flex-col gap-2">
                                        <div class="flex gap-2 items-center">
                                            <h4 class="font-medium">Response</h4>
                                            <Button onclick={() => fullScreenDetails = selectedEvent.response.result} variant="ghost" size="icon">
                                                <Maximize_2 />
                                            </Button>
                                        </div>
                                        <div class="overflow-auto max-h-[45vh]">
                                            <JSONEditor mode={Mode.text} content={{text: undefined, json: selectedEvent.response.result}} readOnly navigationBar={false}/>
                                        </div>
                                    </div>
                                {:else if selectedEvent.exception}
                                    <div class="flex flex-col gap-2">
                                        <h4 class="font-medium text-red-500">Exception</h4>
                                        <div class="border border-red-200 rounded-md p-3 bg-red-50 dark:bg-red-900/20 overflow-auto max-h-[45vh]">
                                            <pre class="text-xs whitespace-pre-wrap text-red-600 dark:text-red-400">{selectedEvent.exception.exception}</pre>
                                        </div>
                                    </div>
                                {/if}
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>
    <Dialog.Root open={!!fullScreenDetails} onOpenChange={() => fullScreenDetails = null}>
        <Dialog.Content onOpenAutoFocus={(e) => e.preventDefault()} class="max-w-[95wv] w-[95vw] h-[95vh] p-8">
                <JSONEditor content={{text: undefined, json: fullScreenDetails}} readOnly navigationBar={false}/>
        </Dialog.Content>
    </Dialog.Root>
