<script lang="ts">
	import type { CallGroup, Event } from './types';
	import { EventType } from './types';

	let {
		eventGroup,
        rects
	} = $props<{
		eventGroup: CallGroup;
        rects: {
            containerRect: DOMRect;
            lifelineRect: DOMRect;
            eventBoxRect: DOMRect;
        }
	}>();

	let coordinates = $derived.by(calculateCoordinates);
	let isException = $derived(!!eventGroup?.exception);
    let {containerRect, lifelineRect, eventBoxRect} = $derived(rects);

	function getStrokeClass(event: Event) {
		switch (event.event_type) {
			case EventType.EXCEPTION:
				return "stroke-red-400 dark:stroke-red-600";
			default:
				 return "stroke-gray-500 dark:stroke-gray-300";
		}
	}

    function getTextClass(event: Event) {
		switch (event.event_type) {
			case EventType.EXCEPTION:
				return "fill-red-400 dark:fill-red-600";
			default:
				 return "fill-gray-500 dark:fill-gray-400";
		}
	}

	function getMarkerId(event: Event) {
		if (!event) return "arrowhead-call";
		
		switch (event.event_type) {
			case EventType.EXCEPTION:
				return "arrowhead-response-exception";
			case EventType.RESULT:
				return "arrowhead-response-result";
			case EventType.CALL:
				return "arrowhead-call";
			default:
				return "arrowhead-call";
		}
	}
	

    type Coordinates = {
        call?: {
                startX: number;
                startY: number;
                endX: number;
                endY: number;
                midX: number;
                midY: number;
            };
            response?: {
                startX: number;
                startY: number;
                endX: number;
                endY: number;
                midX: number;
                midY: number;
            };
    }

	function calculateCoordinates(): Coordinates {
        let yOffset = 5;
        if(containerRect && eventBoxRect && lifelineRect){
            const containerBoundingTop = containerRect.top;
            const containerBoundingLeft = containerRect.left;

            const eventBoxTop = eventBoxRect.top - containerBoundingTop + yOffset;
            const eventBoxBottom = eventBoxRect.bottom - containerBoundingTop - yOffset;
            const eventBoxLeft = eventBoxRect.left - containerBoundingLeft;
            const eventBoxRight = eventBoxRect.right - containerBoundingLeft;
            const callerLifelineLeft = lifelineRect.left - containerBoundingLeft;
            const callerLifelineRight = lifelineRect.right - containerBoundingLeft;
            const isCallerLeftOfModule = callerLifelineLeft < eventBoxLeft;


            // For call events (top of the box)
            const result: Coordinates = {
                call: {
                    startX: isCallerLeftOfModule ? callerLifelineRight + eventBoxRect.width / 2: callerLifelineLeft - eventBoxRect.width / 2,
                    startY: eventBoxTop,
                    endX: isCallerLeftOfModule ? eventBoxLeft : eventBoxRight,
                    endY: eventBoxTop,
                    midX: isCallerLeftOfModule ? 
                        (callerLifelineRight + eventBoxRect.width + eventBoxLeft) / 2 : 
                        (callerLifelineLeft + eventBoxRight) / 2,
                    midY: eventBoxTop + 15
                }
            }

            // For response/exception events (bottom of the box)
            if (eventGroup.response || eventGroup.exception) {
                result.response = {
                    startX: isCallerLeftOfModule ? eventBoxLeft : eventBoxRight,
                    startY: eventBoxBottom,
                    endX: isCallerLeftOfModule ? callerLifelineRight + eventBoxRect.width/2 : callerLifelineLeft - eventBoxRect.width/2,
                    endY: eventBoxBottom,
                    midX: isCallerLeftOfModule ? 
                        (callerLifelineRight + eventBoxRect.width + eventBoxLeft) / 2 : 
                        (callerLifelineLeft + eventBoxRight) / 2,
                    midY: eventBoxBottom - 5
                }
            }

            return result;
        }else{
            return {};
        }
	}
</script>

{#if coordinates.call}
<line
	x1={coordinates.call.startX}
	y1={coordinates.call.startY}
	x2={coordinates.call.endX}
	y2={coordinates.call.endY}
	class={getStrokeClass(eventGroup.call)}
	stroke-width="1"
	stroke-dasharray={isException ? "5,5" : ""}
	marker-end={`url(#${getMarkerId(eventGroup.call)})`}
/>
<text 
	x={coordinates.call.midX} 
	y={coordinates.call.midY} 
	text-anchor="middle" 
	class={`text-xs ${getTextClass(eventGroup.call)}`}
>
	{eventGroup.call.method_name}
</text>
{/if}

{#if coordinates.response}
<line
	x1={coordinates.response.startX}
	y1={coordinates.response.startY}
	x2={coordinates.response.endX}
	y2={coordinates.response.endY}
	class={getStrokeClass(eventGroup.response || eventGroup.exception)}
	stroke-width="1"
	stroke-dasharray={isException ? "5,5" : ""}
	marker-end={`url(#${getMarkerId(eventGroup.response || eventGroup.exception)})`}
/>
<text 
	x={coordinates.response.midX} 
	y={coordinates.response.midY} 
	text-anchor="middle" 
	class={`text-xs fill-gray-300 dark:fill-gray-700`}
>
    {(((eventGroup.response || eventGroup.exception).time - eventGroup.call.time) * 1000).toFixed(2)}ms
</text>
{/if}
