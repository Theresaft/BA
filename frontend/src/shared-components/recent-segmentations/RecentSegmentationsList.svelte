<script>
    import { RecentSegmentations } from "../stores/Store.js"
    import HideSymbol from "./svg/HideSymbol.svelte"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"
    import RecentSegmentationsTitle from "./RecentSegmentationsTitle.svelte"
</script>

<div>
    {#each $RecentSegmentations as segmentationData}
        <RecentSegmentationsEntry {segmentationData}/>
    {/each}
</div>

<style>
    .header-wrapper {
        display: flex;
        flex-direction: row;
    }
</style>