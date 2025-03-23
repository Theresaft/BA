<script>
    import {  Projects, UserSettings } from "../../stores/Store.js"
    import { onMount } from "svelte"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"

    let sortedSegmentations = []
    // The current time at the time of loading the RecentSegmentationsList
    let currentTime = null

    $: noSegmentationsAvailable = sortedSegmentations.length === 0

    /**
     * This reactive block computes the recent segmentations whenever a segmentation changes. They are automatically sorted by timestamp
     * and only contain as many entries as given by numberDisplayedRecentSegmentations.
    */
    $: {
        let segmentations = []

        for (let project of $Projects) {
            segmentations = [...segmentations, ...project.segmentations]
        }

        // Sort the segmentations in-place so that the latest segmentation is the first in the list, regardless of the project.
        segmentations.sort((segA, segB) => segA.segmentationID < segB.segmentationID)

        // This doesn't cause an index out of bounds exception.
        segmentations = segmentations.slice(0, parseInt($UserSettings["numberDisplayedRecentSegmentations"]))
        sortedSegmentations = segmentations
    }

    onMount(() => {
        currentTime = new Date()
    })
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