<script>
    import { RecentSegmentations } from "../../stores/Store.js"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"
</script>

<div>
    {#each $RecentSegmentations as segmentationData}
        <RecentSegmentationsEntry on:open-viewer {segmentationData}/>
    {/each}
</div>

<style>
    .header-wrapper {
        display: flex;
        flex-direction: row;
    }
</style>