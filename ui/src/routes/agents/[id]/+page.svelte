<script lang="ts">
	import PageHeader from "$lib/components/custom/PageHeader.svelte";
	import {page} from '$app/state';
</script>



<PageHeader title={page.params.id} />