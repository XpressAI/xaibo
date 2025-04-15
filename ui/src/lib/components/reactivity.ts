import { createSubscriber } from 'svelte/reactivity';
import {on} from "svelte/events";

export class BoundingBox {
    #ref;
    #subscribe;
    constructor(ref: HTMLElement) {
        this.#ref = ref;
        this.#subscribe = createSubscriber((update) => {
            if(this.#ref){
                const off = on(window, 'resize', update);
                const observer = new ResizeObserver(update);
                observer.observe(this.#ref);

                return () => {
                    observer.disconnect();
                    off();
                }
            }else{
                return () => {};
            }
        });
    }
    get current(){
        this.#subscribe();
        if(this.#ref){
            const bbox =  this.#ref.getBoundingClientRect();
            return bbox;
        }else{
            return {
                top: 0,
                right: 0,
                left: 0,
                bottom: 0,
                height: 0,
                width: 0,
                y: 0,
                x: 0
            } as DOMRect;
        }
    }
}