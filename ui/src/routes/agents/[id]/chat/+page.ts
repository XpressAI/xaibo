import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
	// The agent ID is available via params.id
	// No data loading needed for the chat page - agent is fetched on demand
	return {
		agentId: params.id
	};
};
