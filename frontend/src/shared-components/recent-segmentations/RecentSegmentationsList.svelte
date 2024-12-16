<script>
    import { RecentSegmentations } from "../../stores/Store.js"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"

    $: noSegmentationsAvailable = $RecentSegmentations.length === 0
</script>

<div class="container">
    {#if noSegmentationsAvailable}
        <p class="no-projects-text">
            Es sind keine kürzlich erstellten Segmentierungen vorhanden.
        </p>
    {:else}
        {#each $RecentSegmentations.slice().reverse() as segmentation}
            <RecentSegmentationsEntry on:open-viewer {segmentation}/>
        {/each}
    {/if}
</div>

<style>
    .container {
        margin-top: 13px;
    }
</style>