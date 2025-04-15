import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ parent }) => {
	const parentData = await parent();
	return {
		breadcrumbs: parentData.breadcrumbs.concat({
			name: 'Agents',
			href: '/agents'
		})
	};
};
