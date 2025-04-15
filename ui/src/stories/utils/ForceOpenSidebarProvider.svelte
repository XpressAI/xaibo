<script lang="ts">
	import { SidebarProvider } from '$lib/components/ui/sidebar';
	let { children } = $props();
</script>

<SidebarProvider open={true}>
	{@render children?.()}
</SidebarProvider>
