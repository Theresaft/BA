<script>
    import {  Projects } from "../../stores/Store.js"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"

    let sortedSegmentations = []

    $: noSegmentationsAvailable = $Projects.flatMap(project => project.segmentations).length === 0

    $: {
        let segmentations = []

        for (let project of $Projects) {
            segmentations = [...segmentations, ...project.segmentations]
        }

        // Sort the segmentations in-place so that the latest segmentation is the first in the list, regardless of the project.
        segmentations.sort((segA, segB) => new Date(segA.dateTime).getTime() < new Date(segB.dateTime).getTime())
        sortedSegmentations = segmentations
    }
</script>

<div class="container">
    {#if noSegmentationsAvailable}
        <p class="no-projects-text">
            Es sind keine kürzlich erstellten Segmentierungen vorhanden.
        </p>
    {:else}
        {#each sortedSegmentations as segmentation}
            <RecentSegmentationsEntry on:open-viewer {segmentation}/>
        {/each}
    {/if}
</div>

<style>
    .container {
        margin-top: 13px;
    }
</style>