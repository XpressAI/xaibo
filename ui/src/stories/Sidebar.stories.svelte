<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import {
		Root,
		Header,
		Content,
		Menu,
		MenuItem,
		MenuButton,
		MenuSub,
		MenuSubItem,
		MenuSubButton,
		Group,
		GroupLabel,
		Rail,
		Separator
	} from '$lib/components/ui/sidebar';
	import ForceOpenSidebarProvider from './utils/ForceOpenSidebarProvider.svelte';
	import { fn } from '@storybook/test';
	import Bot from '@lucide/svelte/icons/bot';
	import PlusSquare from '@lucide/svelte/icons/plus-square';
	import Home from '@lucide/svelte/icons/home';
	import Settings from '@lucide/svelte/icons/settings';
	import Users from '@lucide/svelte/icons/users';
	import FileText from '@lucide/svelte/icons/file-text';
	import { Button } from '$lib/components/ui/button';

	// Sample data for sidebar navigation
	const sampleData = {
		navMain: [
			{
				title: 'Dashboard',
				url: '/dashboard',
				icon: Home,
				isActive: true
			},
			{
				title: 'Users',
				url: '/users',
				icon: Users,
				items: [
					{
						title: 'Team Members',
						url: '/users/team',
						isActive: false
					},
					{
						title: 'Administrators',
						url: '/users/admins',
						isActive: false
					}
				]
			},
			{
				title: 'Documents',
				url: '/documents',
				icon: FileText,
				items: [
					{
						title: 'Reports',
						url: '/documents/reports',
						isActive: false
					},
					{
						title: 'Invoices',
						url: '/documents/invoices',
						isActive: false
					}
				]
			},
			{
				title: 'Settings',
				url: '/settings',
				icon: Settings
			}
		]
	};

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'UI/Sidebar',
		component: Root,
		tags: ['autodocs'],
		argTypes: {},
		args: {},
		decorators: [() => ForceOpenSidebarProvider]
	});
</script>

{#snippet defaultSidebar()}
	<Root>
		<Header>
			<Menu>
				<MenuItem>
					<MenuButton size="lg">
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
					</MenuButton>
				</MenuItem>
			</Menu>
		</Header>
		<Content>
			<Group>
				<Menu>
					{#each sampleData.navMain as item (item.title)}
						<MenuItem>
							<div class="flex">
								<MenuButton class="font-medium" isActive={item.isActive}>
									{#snippet child({ props })}
										<a href={item.url} {...props}>
											{#if item.icon}
												<svelte:component this={item.icon} class="mr-2 size-4" />
											{/if}
											{item.title}
										</a>
									{/snippet}
								</MenuButton>
								{#if item.items}
									<Button variant="ghost" title="Add">
										<PlusSquare class="size-4" />
									</Button>
								{/if}
							</div>
							{#if item.items?.length}
								<MenuSub>
									{#each item.items as subItem (subItem.title)}
										<MenuSubItem>
											<MenuSubButton isActive={subItem.isActive}>
												{#snippet child({ props })}
													<a href={subItem.url} {...props}>{subItem.title}</a>
												{/snippet}
											</MenuSubButton>
										</MenuSubItem>
									{/each}
								</MenuSub>
							{/if}
						</MenuItem>
					{/each}
				</Menu>
			</Group>
		</Content>
		<Rail />
	</Root>
{/snippet}

{#snippet simpleSidebar()}
	<Root>
		<Header>
			<Menu>
				<MenuItem>
					<MenuButton>
						{#snippet child({ props })}
							<a href="/" {...props}>
								<Bot class="mr-2 size-4" />
								Xaibo
							</a>
						{/snippet}
					</MenuButton>
				</MenuItem>
			</Menu>
		</Header>
		<Content>
			<Menu>
				<MenuItem>
					<MenuButton isActive={true}>
						{#snippet child({ props })}
							<a href="/dashboard" {...props}>
								<Home class="mr-2 size-4" />
								Dashboard
							</a>
						{/snippet}
					</MenuButton>
				</MenuItem>
				<MenuItem>
					<MenuButton>
						{#snippet child({ props })}
							<a href="/settings" {...props}>
								<Settings class="mr-2 size-4" />
								Settings
							</a>
						{/snippet}
					</MenuButton>
				</MenuItem>
			</Menu>
		</Content>
		<Rail />
	</Root>
{/snippet}

{#snippet withGroupsSidebar()}
	<Root>
		<Header>
			<Menu>
				<MenuItem>
					<MenuButton>
						{#snippet child({ props })}
							<a href="/" {...props}>
								<Bot class="mr-2 size-4" />
								Xaibo
							</a>
						{/snippet}
					</MenuButton>
				</MenuItem>
			</Menu>
		</Header>
		<Content>
			<Group>
				<GroupLabel>Main Navigation</GroupLabel>
				<Menu>
					<MenuItem>
						<MenuButton isActive={true}>
							{#snippet child({ props })}
								<a href="/dashboard" {...props}>
									<Home class="mr-2 size-4" />
									Dashboard
								</a>
							{/snippet}
						</MenuButton>
					</MenuItem>
				</Menu>
			</Group>
			<Separator />
			<Group>
				<GroupLabel>Administration</GroupLabel>
				<Menu>
					<MenuItem>
						<MenuButton>
							{#snippet child({ props })}
								<a href="/users" {...props}>
									<Users class="mr-2 size-4" />
									Users
								</a>
							{/snippet}
						</MenuButton>
						<MenuSub>
							<MenuSubItem>
								<MenuSubButton>
									{#snippet child({ props })}
										<a href="/users/team" {...props}>Team Members</a>
									{/snippet}
								</MenuSubButton>
							</MenuSubItem>
							<MenuSubItem>
								<MenuSubButton>
									{#snippet child({ props })}
										<a href="/users/admins" {...props}>Administrators</a>
									{/snippet}
								</MenuSubButton>
							</MenuSubItem>
						</MenuSub>
					</MenuItem>
					<MenuItem>
						<MenuButton>
							{#snippet child({ props })}
								<a href="/settings" {...props}>
									<Settings class="mr-2 size-4" />
									Settings
								</a>
							{/snippet}
						</MenuButton>
					</MenuItem>
				</Menu>
			</Group>
		</Content>
		<Rail />
	</Root>
{/snippet}

<Story name="Default" args={{ children: defaultSidebar }} />

<Story name="Simple" args={{ children: simpleSidebar }} />

<Story name="With Groups" args={{ children: withGroupsSidebar }} />
