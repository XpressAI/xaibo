<script module>
    import { defineMeta } from '@storybook/addon-svelte-csf';
    import ModuleConfig from '../routes/agents/[id]/config/ModuleConfig.svelte';
    import { fn } from '@storybook/test';

    const { Story } = defineMeta({
        title: 'UI/ModuleConfig',
        component: ModuleConfig,
        tags: ['autodocs'],
        args: {
            module: {
                id: 'test-module',
                module: 'test.module.processor',
                provides: ['protocol.v1'],
                uses: ['protocol.v2'],
                config: { key: 'value' }
            },
            index: 0,
            onRemove: fn()
        }
    });
</script>

<Story name="Default" />

<Story 
    name="Empty" 
    args={{
        module: {
            id: '',
            module: '',
            provides: [],
            uses: [],
            config: {}
        }
    }}
/>

<Story 
    name="With Complex Config" 
    args={{
        module: {
            id: 'complex-module',
            module: 'test.module.complex',
            provides: ['protocol.v1', 'protocol.v2'],
            uses: ['protocol.v3', 'protocol.v4'],
            config: {
                nested: {
                    key: 'value',
                    array: [1, 2, 3]
                },
                enabled: true,
                timeout: 1000
            }
        }
    }}
/>
