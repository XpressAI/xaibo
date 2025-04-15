export type Port = {
    protocol: string;
    ref: HTMLElement;
};

export type NodeType = {
    ref?: HTMLElement;
    id: string;
    module: string;
    provides: Port[];
    uses: Port[];
    config: any;
    level?: number;
    isEntry?: boolean;
    isOpen: boolean;
};

export type LinkType = {
    id: string;
    source: string;
    sourcePort: string;
    target: string;
    targetPort: string;
    protocol: string;
};