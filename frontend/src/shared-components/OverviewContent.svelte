<script>
    import FolderSummary from "./FolderSummary.svelte";
    import ModelSelector from "./ModelSelector.svelte";
    import SegmentationNameInput from "./SegmentationNameInput.svelte";
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    export let selectedData = []

    const startSegmentation = () => {
        
    }
</script>

<div>
    <p class="description">
        Dies sind die ausgewählten DICOM-Sequenzen:
    </p>
    <FolderSummary data={selectedData}/>
    <ModelSelector/>
    <SegmentationNameInput/>
    <div class="overview-button-container">
        <button class="main-button back-button" on:click={() => dispatch("goBack")}>
            Zurück
        </button>
        <button class="confirm-button continue-button" on:click={startSegmentation}>
            Segmentierung starten
        </button>
    </div>
</div>

<style>
    .description {
        margin: 20px 0;
    }
    .overview-button-container {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .back-button {
        max-width: 16.5%;
    }
    .continue-button {
        max-width: 16.5%;
    }
</style>