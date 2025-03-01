<script>
    import {  Projects } from "../../stores/Store.js"
    import { onMount } from "svelte"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"

    // The maximum number of hours after which a segmentation is still considered "recent".
    const maximumRecentSegmentationAgeHours = 24 * 1
    // The maximum number of allowed recent segmentations
    const maximumRecentSegmentationsElements = 10

    let sortedSegmentations = []
    // The current time at the time of loading the RecentSegmentationsList
    let currentTime = null

    $: noSegmentationsAvailable = $Projects.flatMap(project => project.segmentations).length === 0

    /**
     * This reactive block computes the recent segmentations whenever a segmentation changes. We only want to get the ten most recent segmentations
     * or those that are not older than a day. If there more than ten recent segmentations newer than one day, we only show the ten most recent ones.
    */
    $: {
        let segmentations = []

        for (let project of $Projects) {
            segmentations = [...segmentations, ...project.segmentations]
        }

        // Sort the segmentations in-place so that the latest segmentation is the first in the list, regardless of the project.
        segmentations.sort((segA, segB) => new Date(segA.dateTime).getTime() < new Date(segB.dateTime).getTime())

        // Limit segmentation list to 10. This doesn't cause an index out of bounds exception.
        segmentations = segmentations.slice(0, maximumRecentSegmentationsElements)

        segmentations = segmentations.filter(seg => {
            const differenceInHours = Math.floor((currentTime - new Date(seg.dateTime)) / (1000 * 60 * 60))
            return differenceInHours < maximumRecentSegmentationAgeHours
        })

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