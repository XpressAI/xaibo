<script lang="ts">
    import { goto } from '$app/navigation';
    import AgentConfigRenderer from '$lib/components/custom/AgentConfigRenderer.svelte';
    import * as Table from '$lib/components/ui/table';
    import * as Select from '$lib/components/ui/select';
    import { Button } from '$lib/components/ui/button';
    import ChevronRight from '@lucide/svelte/icons/chevron-right';
    import CircleDot from '@lucide/svelte/icons/disc';
    import StopCircle from '@lucide/svelte/icons/stop-circle';
    import MessageSquare from '@lucide/svelte/icons/message-square';
    import { Modal } from '$lib/components/ui/modal';
    import ConversationPrompt from '$lib/components/custom/ConversationPrompt.svelte';
    import Play from '@lucide/svelte/icons/play';
	import { untrack } from 'svelte';

    let {data} = $props();
    let {AgentConfig} = $derived(data);
    let {agentConfig} = $derived($AgentConfig.data);

    let isRecording = $state(false);
    let showDialog = $state(false);
    let systemPrompt = $state('');
    let messages = $state([]);
    let selectedTemplate = $state("custom");

    const promptTemplates = [
        { value: 'custom', label: 'Custom Prompt' },
        { 
            value: 'meeting-summary',
            label: 'Meeting Summary',
            prompt: 'You are a helpful assistant that summarizes meetings. Please help me summarize the key points from my meeting.',
            initialMessages: [
                {
                    role: 'user',
                    content: 'I just finished a meeting and need help summarizing the key points.',
                },
                {
                    role: 'assistant', 
                    content: 'I\'ll help you summarize your meeting. Please share the main topics and discussions from your meeting, and I\'ll help organize the key points.'
                }
            ]
        },
        {
            value: 'task-manager',
            label: 'Task Manager',
            prompt: 'You are a task management assistant. Help me organize and track my tasks effectively.',
            initialMessages: [
                {
                    role: 'user',
                    content: 'I need help organizing my tasks and setting priorities.',
                },
                {
                    role: 'assistant',
                    content: 'I\'ll help you manage your tasks. Could you list out your current tasks and any deadlines or priorities you have in mind?',
                },
                {
                    role: 'user',
                    content: 'I have several tasks for my current project: implement user authentication, design the dashboard UI, and set up the database schema. The authentication needs to be done by next week.',
                }
            ]
        }
    ];
    $effect(() => {
        selectedTemplate;
        untrack(() => {
            if(selectedTemplate != "custom"){
                let tpl = promptTemplates.find(it => it.value == selectedTemplate)
                messages = tpl?.initialMessages || [];
                systemPrompt = tpl?.prompt || "";
            }
        })
    })
    $effect(() => {
        messages;
        systemPrompt;
        untrack(() => {
            if(selectedTemplate != "custom"){
                let tpl = promptTemplates.find(it => it.value == selectedTemplate)
                if(JSON.stringify(messages) != JSON.stringify(tpl?.initialMessages) || systemPrompt != tpl?.prompt) {
                    selectedTemplate = "custom"
                }
            }
        });
    })


    // TODO: Replace with actual interactions data
    let interactions = $state([
        {
            id: '1',
            timestamp: new Date('2024-01-20T10:30:00'),
            type: 'text',
            message: 'What\'s on my agenda today?'
        },
        {
            id: '2', 
            timestamp: new Date('2024-01-20T11:15:00'),
            type: 'text',
            message: 'Share a summary of today\'s standup...'
        }
    ]);

    function handleRowClick(id: string) {
        goto(`/agents/${agentConfig.id}/monitoring/${id}`);
    }

    function toggleRecording() {
        isRecording = !isRecording;
        // TODO: Implement actual recording logic
    }

    function handleGenerateResponse(prompt: string, messages: any[], callback: (m: any) => void) {
        // TODO: Implement actual response generation
    }

    function runAndRecord() {
        isRecording = true;
        handleGenerateResponse(systemPrompt, messages, (response) => {
            // TODO: Handle the response and recording
            isRecording = false;
            showDialog = false;
        });
    }
</script>

<div class="container mx-auto p-6">
    <div class="flex items-center justify-between mb-8">
        <h1 class="text-3xl font-bold">Agent Monitoring: {agentConfig.id}</h1>
    </div>

    <div class="mb-12 bg-gray-50 border rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">Current Configuration</h2>
        <AgentConfigRenderer config={agentConfig} />
    </div>

    <div>
        <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-semibold">Interaction History</h2>
            <div class="flex gap-2">
                <Button 
                    variant="outline"
                    onclick={() => showDialog = true}
                >
                    <MessageSquare size={16} class="mr-2" />
                    New Interaction
                </Button>
                <Button 
                    variant={isRecording ? "destructive" : "default"}
                    onclick={toggleRecording}
                >
                    {#if isRecording}
                        <StopCircle size={16} />
                        Stop Recording
                    {:else}
                        <CircleDot size={16} />
                        Start Recording
                    {/if}
                </Button>
            </div>
        </div>
        <Table.Root>
            <Table.Header>
                <Table.Row>
                    <Table.Head>Time</Table.Head>
                    <Table.Head>Date</Table.Head>
                    <Table.Head>Type</Table.Head>
                    <Table.Head>Message</Table.Head>
                    <Table.Head></Table.Head>
                </Table.Row>
            </Table.Header>
            <Table.Body>
                {#each interactions as interaction}
                    <Table.Row class="cursor-pointer hover:bg-muted" onclick={() => handleRowClick(interaction.id)}>
                        <Table.Cell>{interaction.timestamp.toLocaleTimeString()}</Table.Cell>
                        <Table.Cell>{interaction.timestamp.toLocaleDateString()}</Table.Cell>
                        <Table.Cell class="capitalize">{interaction.type}</Table.Cell>
                        <Table.Cell>{interaction.message}</Table.Cell>
                        <Table.Cell>
                            <Button variant="ghost" size="icon">
                                <ChevronRight size={16} />
                            </Button>
                        </Table.Cell>
                    </Table.Row>
                {/each}
            </Table.Body>
        </Table.Root>
    </div>
</div>

<Modal bind:open={showDialog}>
    <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">New Interaction</h2>
        <div class="mb-4">
            <label class="block text-sm text-gray-600 mb-2">
                Choose a template to pre-fill the conversation
            
                <Select.Root type="single" bind:value={selectedTemplate}>
                    <Select.Trigger class="w-full">
                        {#if selectedTemplate}
                            {promptTemplates.find(it => it.value === selectedTemplate)?.label}
                        {:else}
                            Select a template
                        {/if}
                    </Select.Trigger>
                    <Select.Content>
                        {#each promptTemplates as template}
                            <Select.Item value={template.value}>{template.label}</Select.Item>
                        {/each}
                    </Select.Content>
                </Select.Root>
            </label>
        </div>
        <ConversationPrompt
            bind:systemPrompt={systemPrompt}
            bind:messages={messages}
            onGenerateResponse={handleGenerateResponse}
        />
        <div class="mt-4 flex justify-end">
            <Button onclick={runAndRecord} disabled={isRecording}>
                <Play size={16} class="mr-2" />
                Run and Record
            </Button>
        </div>
    </div>
</Modal>
