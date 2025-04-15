<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import {
		Breadcrumb,
		BreadcrumbList,
		BreadcrumbItem,
		BreadcrumbLink,
		BreadcrumbSeparator,
		BreadcrumbPage,
		BreadcrumbEllipsis
	} from '$lib/components/ui/breadcrumb';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import File from '@lucide/svelte/icons/file';
	import Home from '@lucide/svelte/icons/home';
	import { MediaQuery } from 'svelte/reactivity';
	import * as Drawer from '$lib/components/ui/drawer';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { buttonVariants } from '$lib/components/ui/button';

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'UI/Breadcrumb',
		component: Breadcrumb,
		tags: ['autodocs'],
		argTypes: {},
		args: {
			children: defaultBreadcrumb
		}
	});

	const items = [
		{ href: '#', label: 'Home' },
		{ href: '#', label: 'Documentation' },
		{ href: '#', label: 'Building Your Application' },
		{ href: '#', label: 'Data Fetching' },
		{ label: 'Caching and Revalidating' }
	];

	const ITEMS_TO_DISPLAY = 3;

	let open = $state(false);
	let isDesktop = new MediaQuery('(min-width: 768px)');
</script>

{#snippet defaultBreadcrumb()}
	<Breadcrumb>
		<BreadcrumbList>
			<BreadcrumbItem>
				<BreadcrumbLink href="/">Home</BreadcrumbLink>
			</BreadcrumbItem>
			<BreadcrumbSeparator />
			<BreadcrumbItem>
				<BreadcrumbLink href="/components">Components</BreadcrumbLink>
			</BreadcrumbItem>
			<BreadcrumbSeparator />
			<BreadcrumbItem>
				<BreadcrumbPage>Breadcrumb</BreadcrumbPage>
			</BreadcrumbItem>
		</BreadcrumbList>
	</Breadcrumb>
{/snippet}

{#snippet ellipsisBreadcrumb()}
	<Breadcrumb>
		<BreadcrumbList>
			<BreadcrumbItem>
				<BreadcrumbLink href="/">Home</BreadcrumbLink>
			</BreadcrumbItem>
			<BreadcrumbSeparator />
			<BreadcrumbItem>
				<BreadcrumbEllipsis />
			</BreadcrumbItem>
			<BreadcrumbSeparator />
			<BreadcrumbItem>
				<BreadcrumbLink href="/components/ui">UI</BreadcrumbLink>
			</BreadcrumbItem>
			<BreadcrumbSeparator />
			<BreadcrumbItem>
				<BreadcrumbPage>Breadcrumb</BreadcrumbPage>
			</BreadcrumbItem>
		</BreadcrumbList>
	</Breadcrumb>
{/snippet}

{#snippet responsiveBreadcrumb()}
	<div>
		<Breadcrumb>
			<BreadcrumbList>
				<BreadcrumbItem>
					<BreadcrumbLink href={items[0].href}>
						{items[0].label}
					</BreadcrumbLink>
				</BreadcrumbItem>
				<BreadcrumbSeparator />
				{#if items.length > ITEMS_TO_DISPLAY}
					<BreadcrumbItem>
						{#if isDesktop.current}
							<DropdownMenu.Root bind:open>
								<DropdownMenu.Trigger class="flex items-center gap-1" aria-label="Toggle menu">
									<BreadcrumbEllipsis class="size-4" />
								</DropdownMenu.Trigger>
								<DropdownMenu.Content align="start">
									{#each items.slice(1, -2) as item}
										<DropdownMenu.Item>
											<a href={item.href ? item.href : '#'}>
												{item.label}
											</a>
										</DropdownMenu.Item>
									{/each}
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						{:else}
							<Drawer.Root bind:open>
								<Drawer.Trigger aria-label="Toggle Menu">
									<BreadcrumbEllipsis class="size-4" />
								</Drawer.Trigger>
								<Drawer.Content>
									<Drawer.Header class="text-left">
										<Drawer.Title>Navigate to</Drawer.Title>
										<Drawer.Description>Select a page to navigate to.</Drawer.Description>
									</Drawer.Header>
									<div class="grid gap-1 px-4">
										{#each items.slice(1, -2) as item}
											<a href={item.href ? item.href : '#'} class="py-1 text-sm">
												{item.label}
											</a>
										{/each}
									</div>
									<Drawer.Footer class="pt-4">
										<Drawer.Close class={buttonVariants({ variant: 'outline' })}>
											Close
										</Drawer.Close>
									</Drawer.Footer>
								</Drawer.Content>
							</Drawer.Root>
						{/if}
					</BreadcrumbItem>
					<BreadcrumbSeparator />
				{/if}

				{#each items.slice(-ITEMS_TO_DISPLAY + 1) as item}
					<BreadcrumbItem>
						{#if item.href}
							<BreadcrumbLink href={item.href} class="max-w-20 truncate md:max-w-none">
								{item.label}
							</BreadcrumbLink>
							<BreadcrumbSeparator />
						{:else}
							<BreadcrumbPage class="max-w-20 truncate md:max-w-none">
								{item.label}
							</BreadcrumbPage>
						{/if}
					</BreadcrumbItem>
				{/each}
			</BreadcrumbList>
		</Breadcrumb>
	</div>
{/snippet}

<Story name="Default" args={{ children: defaultBreadcrumb }} />

<Story name="With Ellipsis" args={{ children: ellipsisBreadcrumb }} />

<Story name="Responsive" args={{ children: responsiveBreadcrumb }} />
