<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import PageHeader from '$lib/components/custom/PageHeader.svelte';
	import { fn } from '@storybook/test';

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'Custom/PageHeader',
		component: PageHeader,
		tags: ['autodocs'],
		argTypes: {
			title: {
				control: 'text',
				description: 'The title of the page header'
			},
			subtitle: {
				control: 'text',
				description: 'Optional subtitle text'
			}
		},
		args: {
			title: 'Page Title',
			subtitle: 'This is a subtitle for the page header'
		}
	});
</script>

<Story name="Default" />

<Story name="Without Subtitle" args={{ subtitle: undefined }} />

<Story
	name="Long Title"
	args={{
		title: 'This is a very long page title that might wrap to multiple lines on smaller screens',
		subtitle: 'A subtitle to accompany the long title'
	}}
/>

<Story
	name="Long Subtitle"
	args={{
		title: 'Page Title',
		subtitle:
			'This is a longer subtitle that provides more detailed information about the page content and might wrap to multiple lines on smaller screens'
	}}
/>
