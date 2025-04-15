<script lang="ts">
    import Settings from '@lucide/svelte/icons/settings';
    import Plus from '@lucide/svelte/icons/plus';
    import Trash2 from '@lucide/svelte/icons/trash-2';
    import { Button } from '$lib/components/ui/button';
    import * as Select from '$lib/components/ui/select';
    import * as Card from '$lib/components/ui/card';
    import { Label } from '$lib/components/ui/label';
    import AgentConfigRenderer from '$lib/components/custom/AgentConfigRenderer.svelte';
    import ModuleConfig from './ModuleConfig.svelte';

    let {data} = $props();
    let {AgentConfig} = $derived(data);
	let {agentConfig} = $derived($AgentConfig.data);
    let config = $state();

    $effect(() => {
        config = agentConfig;
    })

    // Derived state for module/protocol matching
    let protocolProviders = $derived.by(() => {        
        const providers = {};
        config.modules.forEach(module => {
            if (module.provides) {
                module.provides.forEach(protocol => {
                    if (!providers[protocol]) providers[protocol] = [];
                    providers[protocol].push(module.id);
                });
            }
        });
        return providers;
    });

    function addModule() {
        config.modules = [...config.modules, {
            module: '',
            id: '',
            provides: [],
            uses: [],
            config: {}
        }];
    }

    function removeModule(index: number) {
        config.modules = config.modules.filter((_, i) => i !== index);
    }

    function addExchange() {
        if (!config.exchange) config.exchange = [];
        config.exchange = [...config.exchange, {
            module: '',
            protocol: '',
            provider: ''
        }];
    }

    function removeExchange(index: number) {
        config.exchange = config.exchange.filter((_, i) => i !== index);
    }
</script>

{#if config}
<div class="container mx-auto p-6">
    <div class="flex items-center justify-between mb-8">
        <h1 class="text-3xl font-bold">Agent Configuration: {config.id}</h1>
        <Button variant="default" onclick={() => console.log('Save config')}>
            <Settings size={16} class="mr-2" />
            Save Changes
        </Button>
    </div>

    <div class="mb-12 bg-gray-50 border rounded-lg p-6">
        <AgentConfigRenderer config={config} />
    </div>

    <div class="mb-12">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-semibold">Modules</h2>
            <Button size="sm" onclick={addModule} variant="secondary">
                <Plus size={16} class="mr-2" />
                Add Module
            </Button>
        </div>

        {#each config.modules || [] as module, i}
            <ModuleConfig module={module} index={i} onRemove={removeModule} />
        {/each}
    </div>

    <div>
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-semibold">Exchange Configuration</h2>
            <Button size="sm" onclick={addExchange} variant="secondary">
                <Plus size={16} class="mr-2" />
                Add Exchange Config
            </Button>
        </div>

        <div class="grid grid-cols-3 gap-6 mb-4">
            <div class="text-sm font-medium text-gray-500">Module ID</div>
            <div class="text-sm font-medium text-gray-500">Protocol</div>
            <div class="text-sm font-medium text-gray-500">Provider</div>
        </div>
        {#each config.exchange || [] as exchange, i}
            {@const providersByProtocol = (protocolProviders[exchange.protocol] || []).filter(p => p != exchange.module)}
            <div class="mb-4 p-4 border rounded-lg bg-white">
                <div class="grid grid-cols-3 gap-6">
                    <div>
                        <Select.Root type="single" bind:value={exchange.module}>
                            <Select.Trigger class={`w-full ${exchange.module && exchange.module !== '__entry__' && !config.modules.find(m => m.id === exchange.module) ? 'border-red-500' : ''}`}>
                                <span>{exchange.module || 'Select module ID'}</span>
                            </Select.Trigger>
                            <Select.Content>
                                <Select.Item value="__entry__">__entry__</Select.Item>
                                {#each config.modules as module}
                                    <Select.Item value={module.id}>{module.id}</Select.Item>
                                {/each}
                            </Select.Content>
                        </Select.Root>
                    </div>
                    <div>
                        <Select.Root type="single" bind:value={exchange.protocol} disabled={!exchange.module}>
                            <Select.Trigger class="w-full">
                                <span>{exchange.protocol || 'Select protocol'}</span>
                            </Select.Trigger>
                            <Select.Content>
                                {#if exchange.module === '__entry__'}
                                    <Select.Item value="TextMessageHandlerProtocol">TextMessageHandlerProtocol</Select.Item>
                                    <Select.Item value="ImageMessageHandlerProtocol">ImageMessageHandlerProtocol</Select.Item>
                                    <Select.Item value="AudioMessageHandlerProtocol">AudioMessageHandlerProtocol</Select.Item>
                                {:else}
                                    {#each config.modules.find(m => m.id === exchange.module)?.uses || [] as protocol}
                                        <Select.Item value={protocol}>{protocol}</Select.Item>
                                    {/each}
                                {/if}
                            </Select.Content>
                        </Select.Root>
                    </div>
                    <div class="flex gap-2">
                        <Select.Root type="single" bind:value={exchange.provider} disabled={!exchange.module}>
                            <Select.Trigger 
                                class={`w-full ${exchange.provider && !providersByProtocol.includes(exchange.provider) ? 'border-red-500' : ''}`}
                            >
                                <span>{exchange.provider || 'Select provider'}</span>
                            </Select.Trigger>
                            <Select.Content>
                                {#if !providersByProtocol.length}
                                    <Select.Item value="" disabled>No providers available</Select.Item>
                                {:else}
                                    {#each providersByProtocol as provider}
                                        <Select.Item value={provider}>{provider}</Select.Item>
                                    {/each}
                                {/if}
                            </Select.Content>
                        </Select.Root>
                        <Button size="sm" variant="destructive" onclick={() => removeExchange(i)}>
                            <Trash2 size={16} />
                        </Button>
                    </div>
                </div>
            </div>
        {/each}
    </div>
</div>
{/if}