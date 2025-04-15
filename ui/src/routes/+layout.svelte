<script lang="ts">
	import '../app.css';
	import { i18n } from '$lib/i18n';
	import { ParaglideJS } from '@inlang/paraglide-sveltekit';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import * as Breadcrumb from '$lib/components/ui/breadcrumb';
	import { Separator } from '$lib/components/ui/separator';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { page } from '$app/state';
	let { children, data } = $props();
	let breadcrumbs = $derived.by(() => page.data.breadcrumbs);
	let {Agents} = $derived(data)
	let listAgents = $derived($Agents.data?.listAgents);
</script>

<svelte:head>
	{#if breadcrumbs.length > 0}
		<title>{breadcrumbs[breadcrumbs.length - 1].name} | Xaibo</title>
	{:else}
		<title>Xaibo</title>
	{/if}
</svelte:head>

<ParaglideJS {i18n}>
	<Sidebar.Provider>
		<AppSidebar agents={listAgents || []} />
		<Sidebar.Inset>
			<header class="flex h-16 shrink-0 items-center gap-2 border-b">
				<div class="flex items-center gap-2 px-3">
					<Sidebar.Trigger />
					<Separator orientation="vertical" class="mr-2 h-4" />
					<Breadcrumb.Root>
						<Breadcrumb.List>
							{#each breadcrumbs as breadcrumb, i}
								{#if i < breadcrumbs.length - 1}
									<Breadcrumb.Item class="hidden md:block">
										<Breadcrumb.Link href={breadcrumb.href}>{breadcrumb.name}</Breadcrumb.Link>
									</Breadcrumb.Item>
									<Breadcrumb.Separator class="hidden md:block" />
								{:else}
									<Breadcrumb.Item>
										<Breadcrumb.Page>{breadcrumb.name}</Breadcrumb.Page>
									</Breadcrumb.Item>
								{/if}
							{:else}
								<Breadcrumb.Item>
									<Breadcrumb.Page>Overview</Breadcrumb.Page>
								</Breadcrumb.Item>
							{/each}
						</Breadcrumb.List>
					</Breadcrumb.Root>
				</div>
			</header>
			<div class="flex flex-1 flex-col relative">
				<div class="absolute inset-0 overflow-auto p-4 flex flex-col gap-4">
					{@render children()}
				</div>
			</div>
		</Sidebar.Inset>
	</Sidebar.Provider>
</ParaglideJS>
