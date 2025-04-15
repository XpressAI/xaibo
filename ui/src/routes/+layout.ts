import { load_Agents } from '$houdini'
import type { LayoutLoad } from './$types';

export const ssr = false;

export const load: LayoutLoad = async (event) => {
	return {
		breadcrumbs: [] as { name: string; href: string }[],
		...(await load_Agents({event}))
	};
};
