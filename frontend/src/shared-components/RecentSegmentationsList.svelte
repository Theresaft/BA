<script>
    import { RecentSegmentations } from "../stores/Store.js"
    import RecentSegmentationsEntry from "./RecentSegmentationsEntry.svelte"
    import RecentSegmentationsTitle from "./RecentSegmentationsTitle.svelte"
</script>

<div>
    <RecentSegmentationsTitle/>
    {#each $RecentSegmentations as segmentation}
        <RecentSegmentationsEntry {segmentation}/>
    {/each}
</div>

<style>

</style>