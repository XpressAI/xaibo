import type { LayoutLoad } from './$types';
import { load_AgentConfig } from '$houdini'

export const load: LayoutLoad = async (event) => {
	let { parent, params } = event;
	const parentData = await parent();
	return {
		breadcrumbs: parentData.breadcrumbs.concat({
			name: params.id,
			href: `/agents/${params.id}`
		}),
		...(await load_AgentConfig({event, variables: {
			agentId: params.id,
			}}))
	};
};
