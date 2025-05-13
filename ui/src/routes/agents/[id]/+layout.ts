import type { LayoutLoad } from './$types';
import { loadAll, load_AgentConfig, load_DebugTrace } from '$houdini'

export const load: LayoutLoad = async (event) => {
	let { parent, params } = event;
	const parentData = await parent();
	return {
		breadcrumbs: parentData.breadcrumbs.concat({
			name: params.id,
			href: `/agents/${params.id}`
		}),
		...(await loadAll(
			load_AgentConfig({event, variables: {
					agentId: params.id,
				}}),
			load_DebugTrace({event, variables: {
					agentId: params.id,
				}})
		))
	};
};
