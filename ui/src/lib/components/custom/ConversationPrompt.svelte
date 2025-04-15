<script lang="ts">
  import MessageSquare from '@lucide/svelte/icons/message-square';
  import Plus from '@lucide/svelte/icons/plus';
  import Sparkles from '@lucide/svelte/icons/sparkles';
  import ChevronDown from '@lucide/svelte/icons/chevron-down';
  import ChevronRight from '@lucide/svelte/icons/chevron-right';
  import Button from '$lib/components/ui/button/button.svelte';
  import type {Message} from '$lib/components/custom/conversation-prompt/message.svelte';
  import MessageComponent from '$lib/components/custom/conversation-prompt/message.svelte';
  import { untrack } from 'svelte';
  
  type MessageRole = 'user' | 'assistant';
  

  let { systemPrompt = $bindable(''), messages = $bindable([]), onGenerateResponse } = $props<{
    systemPrompt?: string;
    messages?: Message[];
    onGenerateResponse?: (prompt: string, messages: Message[], callback: (m: Message) => void) => void
  }>();
  
  let messageEditStates: boolean[] = $state([]);
  let systemPromptCollapsed = $state(false);

  function toggleSystemPrompt(): void {
    systemPromptCollapsed = !systemPromptCollapsed;
  }

  function addMessage(): void {
    const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
    const newRole: MessageRole = lastMessage ? (lastMessage.role === 'user' ? 'assistant' : 'user') : 'user';
    messageEditStates.push(true);
    messages = [...messages, { role: newRole, content: '' }];
  }
  
  function removeMessage(message: Message): void {
    const idx = messages.indexOf(message);
    messageEditStates.splice(idx, 1);
    messages.splice(idx, 1);
  }
  
  
  let lastMessageEditState:boolean = $state(true);
  function generateResponse(): void {
    const newMessage: Message = $state({
        content: "",
        role: "assistant",
        isStreaming: true
    });
    messageEditStates[messageEditStates.length - 1] = false;
    messageEditStates.push(false);
    messages = [...messages, newMessage];
    onGenerateResponse(systemPrompt, messages, (m: Message) => {
        newMessage.content = m.content;
        newMessage.isStreaming = m.isStreaming
    })
  }
  
  let conversationData = $derived({
    systemPrompt,
    messages: messages.filter((m: Message) => m.content.trim() !== '')
  });
  
  let lastMessageIsUser = $derived(
    messages.length > 0 && messages[messages.length - 1].role === 'user'
  );
</script>

<div class="flex flex-col gap-4 w-full">
  <div class="flex flex-col">
    <div class="flex flex-col gap-2 mb-2 cursor-pointer" onclick={toggleSystemPrompt}>      
        <div class="flex-1 flex items-center gap-2">
            <MessageSquare size={18} />
            <h3 class="text-base font-semibold m-0 flex-1">System Prompt</h3>
            {#if systemPromptCollapsed}
                <ChevronRight size={18} />
            {:else}
                <ChevronDown size={18} />
            {/if}
        </div>
      
      {#if systemPromptCollapsed && systemPrompt}
        <span class="text-xs text-gray-500 truncate max-w-[300px]">{systemPrompt}</span>
      {/if}
      
    </div>
    {#if !systemPromptCollapsed}
      <textarea 
        bind:value={systemPrompt} 
        placeholder="Set the behavior of the assistant..."
        rows="3"
        class="w-full p-3 border border-gray-200 rounded-md font-inherit text-sm resize-vertical bg-white"
      ></textarea>
    {/if}
  </div>
  
  <div class="flex flex-col">
    <div class="flex items-center gap-2 mb-2">
      <MessageSquare size={18} />
      <h3 class="text-base font-semibold m-0">Messages</h3>
    </div>
    
    <div class="flex flex-col gap-2">
      {#each messages as message, i}
        <MessageComponent message={message} onRemove={removeMessage} bind:isEditing={messageEditStates[i]}/>
      {:else}
        <div class="border border-gray-200 border-dashed rounded-md p-4 bg-gray-50 text-center text-gray-500">
            <p class="text-sm">No messages yet.</p>
        </div>
      {/each}
    </div>
    
    {#if messages.length == 0 || !messages[messages.length-1].isStreaming}
    <div class="flex gap-2 mt-2">
    
      <Button 
        variant="outline"
        class="flex items-center justify-center gap-2 p-2 border-dashed border-gray-300 text-sm" 
        onclick={addMessage}
      >
        <Plus size={16} />
        <span>Add Message</span>
      </Button>      
      
      {#if lastMessageIsUser && onGenerateResponse}
        <Button 
          variant="default"
          class="flex items-center justify-center gap-2 p-2 text-sm" 
          onclick={generateResponse}
        >
          <Sparkles size={16} />
          <span>Generate Response</span>
        </Button>
      {/if}
    </div>
    {/if}
  </div>
</div>
