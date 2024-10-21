<script>
    import ArrowUpSymbol from "../svg/ArrowUpSymbol.svelte"
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"
    import SegmentationOverview from "./SegmentationOverview.svelte"

    export let project = {}

    let showingDetails = false
</script>

<div class="project-container">
    <div class="main-view">
        <div class="project-name-container">
            <h3 class="project-name">{project.projectName}</h3>
        </div>
        <div class="file-type-label-container">
            <p class="file-type-label" class:file-type-dicom={project.fileType === "DICOM"} class:file-type-nifti={project.fileType === "NIFTI"}>{project.fileType}</p>
        </div>
        <div class="show-more-button-container">
            <button class="show-more-button" on:click={() => {showingDetails = !showingDetails}} title={showingDetails ? "Details verbergen" : "Details anzeigen"}>
                {#if showingDetails}
                    <ArrowUpSymbol/>
                {:else}
                    <ArrowDownSymbol/>
                {/if}
            </button>
        </div>
    </div>
    <!-- Only if the user wants to see the details of a projects, all of the segmentations will be shown. What will also be shown is a button for adding
     a new segmentation. -->
    {#if showingDetails}
        {#each project.segmentations as segmentation}
            <SegmentationOverview {segmentation}/>
        {/each}
        <button>Segmentierung hinzufügen</button>
    {/if}
</div>

<style>
    .project-container {
        border-bottom: 1px solid var(--font-color-main);
        margin-bottom: 20px;
    }
    .main-view {
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    .show-more-button-container {
        margin-left: 10px;
    }
    .show-more-button,.trash-button {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: inherit;
        border-radius: 7px;
        padding: 10px;
        padding-bottom: 6px;
    }
    .file-type-label-container {
        margin-left: auto;
    }
    .file-type-label {
        width: 60px;
        padding: 5px 11px;
        border-radius: 10px;
        border: 1px solid var(--background-color-navbar);
        text-align: center;
        
        /* This is a fallback color in case neither NIFTI nor DICOM are defined */
        background: var(--button-color-disabled);
    }
    .file-type-label.file-type-dicom {
        background: var(--background-color-dicom);
    }
    .file-type-label.file-type-nifti {
        background: var(--background-color-nifti);
    }
</style>