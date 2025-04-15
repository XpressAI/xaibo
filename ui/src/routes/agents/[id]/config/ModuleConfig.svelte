<script lang="ts">
    import Trash2 from '@lucide/svelte/icons/trash-2';
    import ChevronDown from '@lucide/svelte/icons/chevron-down';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Textarea } from '$lib/components/ui/textarea';
    import * as Card from '$lib/components/ui/card';
    import { Label } from '$lib/components/ui/label';
    import * as Collapsible from '$lib/components/ui/collapsible';

    let { module = $bindable(), index, onRemove } = $props();

    function handleConfigChange(e: Event) {
        const target = e.target as HTMLTextAreaElement;
        try {
            module.config = JSON.parse(target.value || '{}');
            target.classList.remove('border-red-500');
        } catch (err) {
            target.classList.add('border-red-500');
            console.error('Invalid JSON:', err);
        }
    }

    function handleProvidesChange(e: Event) {
        const target = e.target as HTMLTextAreaElement;
        module.provides = target.value.split('\n').filter(Boolean);
    }

    function handleUsesChange(e: Event) {
        const target = e.target as HTMLTextAreaElement;
        module.uses = target.value.split('\n').filter(Boolean);
    }

    let open = $state(!module.id);
</script>

<Card.Root class="mb-4">
    <Collapsible.Root bind:open={open}>
        <Card.Header class="p-4">
            <Collapsible.Trigger class="flex gap-2 items-center w-full">
                <Card.Title>{module.module?.split('.')?.pop() || 'New Module'}</Card.Title>
                <span class="text-sm text-muted-foreground">({module.id || 'No ID'})</span>
                <div class="flex-1"></div>
                <div class="rounded-full hover:bg-muted p-1">
                    <ChevronDown size={20} />
                </div>
            </Collapsible.Trigger>        
        </Card.Header>

        <Collapsible.Content>
            <Card.Content class="-mt-4 p-4">
                <div class="grid gap-4 grid-cols-2">
                    <div>
                        <Label for="module-id-{index}" class="mb-1 block">Module ID</Label>
                        <Input 
                            id="module-id-{index}"
                            placeholder="e.g. processor1"
                            bind:value={module.id}
                        />
                        {#if !module.id}
                            <p class="text-xs text-red-500 mt-1">Module ID is required</p>
                        {/if}
                    </div>
                    <div>
                        <Label for="module-path-{index}" class="mb-1 block">Module Path</Label>
                        <Input 
                            id="module-path-{index}"
                            placeholder="e.g. my_agent.modules.processor"
                            bind:value={module.module}
                        />
                        {#if !module.module}
                            <p class="text-xs text-red-500 mt-1">Module path is required</p>
                        {/if}
                    </div>

                    <div>
                        <Label for="provides-{index}" class="mb-1 block">
                            Provides
                            <span class="text-gray-500">(one per line)</span>
                        </Label>
                        <Textarea 
                            id="provides-{index}"
                            class="h-20 text-sm font-mono"
                            placeholder="e.g.&#10;protocol.v1&#10;protocol.v2"
                            value={module.provides?.join('\n')}
                            onchange={handleProvidesChange}
                        />
                    </div>
                    <div>
                        <Label for="uses-{index}" class="mb-1 block">
                            Uses
                            <span class="text-gray-500">(one per line)</span>
                        </Label>
                        <Textarea 
                            id="uses-{index}"
                            class="h-20 text-sm font-mono"
                            placeholder="e.g.&#10;protocol.v1&#10;protocol.v2"
                            value={module.uses?.join('\n')}
                            onchange={handleUsesChange}
                        />
                    </div>

                    <div class="col-span-2">
                        <Label for="config-{index}" class="mb-1 block">
                            Config
                            <span class="text-gray-500">(JSON format)</span>
                        </Label>
                        <Textarea 
                            id="config-{index}"
                            class="h-20 text-sm font-mono"
                            placeholder="e.g. {JSON.stringify({key: 'value'}, null, 2)}"
                            value={module.config ? JSON.stringify(module.config, null, 2) : ''}
                            onchange={handleConfigChange}
                        />
                    </div>
                </div>
            </Card.Content>
            <Card.Footer class="flex justify-end">
                <Button 
                    size="sm" 
                    variant="destructive" 
                    onclick={() => onRemove(index)}
                    title="Remove Module"
                >
                    <Trash2 size={16} /> Remove Module
                </Button>
            </Card.Footer>
        </Collapsible.Content>
    </Collapsible.Root>
</Card.Root>
