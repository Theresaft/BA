<script>
    import TrashSymbol from "../../shared-components/svg/TrashSymbol.svelte"
    import ArrowUpSymbol from "../svg/ArrowUpSymbol.svelte"
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"
    import SegmentationOverview from "./SegmentationOverview.svelte"
    import Card from "../general/Card.svelte"
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    export let project = {}

    let showingDetails = false

    function deleteProject() {
        // TODO Implement deletion of store variable and ensure deletion in backend!
        console.log("TODO Delete project " + project.projectName)
    }
</script>

<div class="project-container">
    <div class="title-bar">
        <button class="trash-button" on:click={() => deleteProject()}><TrashSymbol/></button>
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
        <div class="segmentation-container">
            {#each project.segmentations as segmentation}
                <div class="segmentation-wrapper">
                    <Card center={true} dropShadow={false} tertiaryBackground={true}>
                        <SegmentationOverview {segmentation}/>
                    </Card>
                </div>
            {/each}
            <button class="button confirm-button add-segmentation-button" on:click={() => dispatch("createSegmentation")}>Segmentierung hinzufügen</button>
        </div>
    {/if}
</div>

<style>
    .project-container {
        border-bottom: 2px solid var(--font-color-main);
        margin-bottom: 20px;
        padding-bottom: 10px;
    }
    .title-bar {
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    .project-name-container {
        margin-left: 20px;
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
    .segmentation-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
    }
    .segmentation-wrapper {
        width: 80%;
    }
    .add-segmentation-button {
        width: 80%;
        padding-top: 14px;
        padding-bottom: 14px;
        font-size: 15px;
        background: var(--background-color-card-tertiary);
        color: var(--button-text-color-secondary);
    }
    .add-segmentation-button:hover {
        background: var(--background-color-card-tertiary-hover);
        color: var(--button-text-color-primary);
    }
</style>