<script>
    import FolderSummaryEntry from "./FolderSummaryEntry.svelte";
    import FolderSummaryTitle from "./FolderSummaryTitle.svelte";
    export let data = []


</script>

<div class="summary">
    <FolderSummaryTitle/>
    {#each data as entry}
        <FolderSummaryEntry data={entry}></FolderSummaryEntry>
    {/each}
</div>

<style>
	.summary {
		display: flex;
		justify-content: center;
		align-items: center;
		flex-direction: column;
		transition: background-color .3s ease;
		padding-left: 0;
		display: flex;
		flex-direction: column;
		padding: 0;
        margin-bottom: 50px;
	}
</style>