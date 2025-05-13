<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar';
	import Bot from '@lucide/svelte/icons/bot';
	import PlusSquare from '@lucide/svelte/icons/plus-square';
	import type { ComponentProps } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import {page} from '$app/state';
	import {active} from '$lib/actions/active.svelte.ts';

	type Agent = {
		id: string;
	}
	type SidebarProps = {
		agents: Agent[]
	}

	let { ref = $bindable(null), agents, ...restProps }: SidebarProps & ComponentProps<typeof Sidebar.Root > = $props();

	let data = $derived({
		navMain: [
			{
				title: 'Agents',
				url: '/agents',
				items: agents.map((x: Agent) => (
					{
						title: x.id,
						url: `/agents/${x.id}`,
						subItems: [
							/*{
								title: 'Configuration',
								url: `/agents/${x.id}/config`,
							},
							{
								title: 'Monitoring',
								url: `/agents/${x.id}/monitoring`,
							},
							{
								title: 'Tasks',
								url: `/agents/${x.id}/tasks`,
							},
							{
								title: 'Memory',
								url: `/agents/${x.id}/memory`,
							},
							{
								title: 'Budget',
								url: `/agents/${x.id}/budget`
							}*/
						]
					}
				))
			},
			/*{
				title: 'Prompt Templates',
				url: '/templates',
				isActive: false,
				items: [
					{
						title: 'Get to Work',
						url: '/templates/1',
					},
					{
						title: "How's it going?",
						url: '/templates/2',
					},
					{
						title: 'Your title here',
						url: '/templeates/3',
					}
				]
			}*/
		]
	});
</script>

<Sidebar.Root bind:ref {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/" {...props}>
							<div
								class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"
							>
								<Bot class="size-6" />
							</div>
							<div class="flex flex-col gap-0.5 leading-none">
								<span class="font-bold tracking-wider">Xaibo</span>
								<span class="font-extralight">AI Agent Workbench</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.Menu>
				{#each data.navMain as groupItem (groupItem.title)}
					<Sidebar.MenuItem>
						<div class="flex">
							<Sidebar.MenuButton class="font-medium">
								{#snippet child({ props })}
									<a href={groupItem.url} {...props} use:active={{activeForSubdirectories: false}}>
										{groupItem.title}
									</a>
								{/snippet}
							</Sidebar.MenuButton>
							<!--<Button variant="ghost" title="Add" href="/agents/create">
								<PlusSquare />
							</Button>-->
						</div>
						{#if groupItem.items?.length}
							<Sidebar.MenuSub>
								{#each groupItem.items as item (item.title)}
									<Sidebar.MenuSubItem>
										<Sidebar.MenuSubButton>
											{#snippet child({ props })}
												<a href={item.url} {...props} use:active={{activeForSubdirectories: false}}>{item.title}</a>
											{/snippet}
										</Sidebar.MenuSubButton>
										{#if page.params.id === item.title && item.subItems}
											<Sidebar.MenuSub>
												{#each item.subItems as subItem}
													<Sidebar.MenuSubItem>
														<Sidebar.MenuSubButton>
															{#snippet child({ props })}
																<a href={subItem.url} {...props} use:active={{activeForSubdirectories: false}}>{subItem.title}</a>
															{/snippet}
														</Sidebar.MenuSubButton>
													</Sidebar.MenuSubItem>
												{/each}
											</Sidebar.MenuSub>
										{/if}
									</Sidebar.MenuSubItem>
								{/each}
							</Sidebar.MenuSub>
						{/if}
					</Sidebar.MenuItem>
				{/each}
			</Sidebar.Menu>
		</Sidebar.Group>
	</Sidebar.Content>
	<Sidebar.Rail />
</Sidebar.Root>
