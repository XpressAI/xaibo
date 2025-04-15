export type CallGroup = {
		call: Event;
		response?: Event;
		exception?: Event;
        parent?: CallGroup;
        start: number;
        length: number;
        ref?: HTMLElement;
        boxRef?: HTMLElement;
}

export enum EventType {
    CALL = "call",
    RESULT = "result",
    EXCEPTION = "exception"
}

export type Event = {
    agent_id: string;
    event_name: string;
    event_type: EventType;
    module_id: string;
    module_class: string;
    method_name: string;
    time: number;
    call_id: string;
    caller_id: string;
    arguments?: Record<string, any>;
    result?: any;
    exception?: string;
};
