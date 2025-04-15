<script lang="ts" module>
    export type MessageRole = 'user' | 'assistant';
    
    export interface Message {
        role: MessageRole;
        content: string;
        isStreaming?: boolean;
    }
</script>

<script lang="ts">
  import User from '@lucide/svelte/icons/user';
  import Bot from '@lucide/svelte/icons/bot';
  import Trash from '@lucide/svelte/icons/trash';
  import Edit from '@lucide/svelte/icons/edit';
  import Check from '@lucide/svelte/icons/check';
  import Button from '$lib/components/ui/button/button.svelte';
	import { untrack } from 'svelte';
  
  
  let { 
    message = $bindable(),
    isEditing = $bindable(),
    onRemove 
} = $props<{
    message: Message;
    isEditing?: boolean;
    onRemove: (m: Message) => void,
  }>();
  $effect(() => {
    untrack(() => isEditing = !message.isStreaming && message.content.length == 0)
  })

  let canEdit = $derived(!message.isStreaming);

  function toggleRole(): void {
    message.role = message.role == "user" ? "assistant" : "user";
  }
  
  function removeMessage(): void {
    onRemove(message);
  }
  
  function toggleEdit(): void {
    if (!canEdit) return;
    isEditing = !isEditing;
  }
</script>

<div class="border border-gray-200 rounded-md p-2 bg-gray-50">
  <div class="flex justify-between items-center gap-2 mb-1">
    <Button 
      variant="secondary"
      size="sm"
      class="flex items-center gap-1 text-xs py-0.5 px-2 h-auto"
      onclick={toggleRole}
      title="Toggle between user and assistant"
    >
      {#if message.role === 'user'}
        <User size={14} />
        <span>User</span>
      {:else}
        <Bot size={14} />
        <span>Assistant</span>
      {/if}
    </Button>
    
    <div class="flex">
      <Button 
        variant="ghost"
        size="icon"
        class="p-0.5 h-6 w-6 text-gray-500 hover:text-blue-500 hover:bg-blue-100"
        onclick={toggleEdit}
        title={isEditing ? "Save changes" : "Edit message"}
        disabled={!canEdit}
      >
        {#if isEditing && canEdit}
          <Check size={14} />
        {:else}
          <Edit size={14} />
        {/if}
      </Button>
      
      <Button 
        variant="ghost"
        size="icon"
        class="p-0.5 h-6 w-6 text-gray-500 hover:text-red-500 hover:bg-red-100"
        onclick={removeMessage}
        title="Remove message"
      >
        <Trash size={14} />
      </Button>
    </div>
  </div>
  
  {#if isEditing && canEdit}
    <textarea 
      bind:value={message.content} 
      placeholder={message.role === 'user' ? "User message..." : "Assistant response..."}
      rows="3"
      class="w-full p-2 border border-gray-200 rounded-md font-inherit text-sm resize-vertical bg-white"
    ></textarea>
  {:else}
    <pre class="w-full p-2 whitespace-pre-wrap text-xs"
    >{message.content || (message.role === 'user' ? "User message..." : "Assistant response...")}{#if message.isStreaming}<span
     class="animate-pulse text-blue-500 font-bold">▋</span
     >{/if}</pre>
  {/if}
</div>
