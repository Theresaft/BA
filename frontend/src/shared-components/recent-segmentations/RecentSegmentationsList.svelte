<script>
    import {  Projects } from "../../stores/Store.js"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"

    $: noSegmentationsAvailable = $Projects.flatMap(project => project.segmentations).length === 0
</script>

<div class="container">
    {#if noSegmentationsAvailable}
        <p class="no-projects-text">
            Es sind keine kürzlich erstellten Segmentierungen vorhanden.
        </p>
    {:else}
        {#each $Projects as project}
            {#each project.segmentations.slice().reverse() as segmentation}
                <RecentSegmentationsEntry on:open-viewer {segmentation}/>
            {/each}
        {/each}
    {/if}
</div>

<style>
    .container {
        margin-top: 13px;
    }
</style>