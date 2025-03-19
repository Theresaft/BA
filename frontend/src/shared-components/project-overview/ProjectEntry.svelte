<script>
    import TrashSymbol from "../../shared-components/svg/TrashSymbol.svelte"
    import ArrowUpSymbol from "../svg/ArrowUpSymbol.svelte"
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"
    import SegmentationOverview from "./SegmentationOverview.svelte"
    import Card from "../general/Card.svelte"
    import Modal from "../general/Modal.svelte"
    import Loading from "../../single-components/Loading.svelte"
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    export let project = {}
    export let reloadSegmentationEntries

    let showDeleteModal = false
    let showingDetails = false
    let showLoadingSymbol = false
    // The segmentation name that is being deleted. If none is being deleted, this is null
    let segmentationNameToDelete = null

    // When the segmentation entry is reloaded, update the loading symbol flag.
    $: reloadSegmentationEntries, showLoadingSymbol = false
    $: reloadSegmentationEntries, segmentationNameToDelete = null

    function deleteClicked() {
        showDeleteModal = true
    }

    /**
     * Send the delete request to the parent component with the given project ID.
     */
    function confirmDelete() {
        dispatch("delete", project.projectID)
        showLoadingSymbol = true
        segmentationNameToDelete = null
    }

    async function deleteSegmentation(e) {
        // We set the loading flag to true and set it to false when the segmentation entry
        // is reloaded.
        showLoadingSymbol = true
        const {segmentationName: segmentationName, segmentationID: segmentationID} = e.detail
        segmentationNameToDelete = segmentationName
        dispatch("deleteSegmentation", {
            projectID: project.projectID,
            projectName: project.projectName,
            segmentationName: segmentationName,
            segmentationID: segmentationID
        })
    }

    function deleteCanceled() {
        showDeleteModal = false
        showLoadingSymbol = false
    }
</script>

<div class="project-container">
    {#if !showLoadingSymbol}
        <div class="title-bar">
            <button class="trash-button" on:click={() => deleteClicked()}><TrashSymbol/></button>

            <div class="project-name-container">
                <h3 class="project-name">{project.projectName}</h3>
            </div>
            <div class="file-type-label-container">
                <p class="file-type-label" class:file-type-dicom={project.fileType === "dicom"} class:file-type-nifti={project.fileType === "nifti"}>{project.fileType.toUpperCase()}</p>
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
                {#key reloadSegmentationEntries}
                    {#each project.segmentations as segmentation}
                        <div class="segmentation-wrapper">
                            <Card center={true} dropShadow={false} tertiaryBackground={true}>
                                <SegmentationOverview on:delete={deleteSegmentation} {segmentation} bind:projectName={project.projectName}/>
                            </Card>
                        </div>
                    {/each}
                {/key}
                <button class="button confirm-button add-segmentation-button" on:click={() => dispatch("createSegmentation")}>Segmentierung hinzufügen</button>
            </div>
        {/if}
    <!-- Show loading symbol if segmentation or project is being deleted -->
    {:else}
        <div class="delete-container">
            <Loading spinnerSizePx={30}></Loading>
            {#if segmentationNameToDelete}
                <div class="delete-text">Segmentierung <strong>{segmentationNameToDelete}</strong> im Projekt <strong>{project.projectName}</strong> wird gelöscht...</div>
            {:else}
                <div class="delete-text">Projekt <strong>{project.projectName}</strong> wird gelöscht...</div>
            {/if}
        </div>
    {/if}
</div>

<Modal bind:showModal={showDeleteModal} on:cancel={deleteCanceled} on:confirm={() => confirmDelete()} cancelButtonText = "Abbrechen" cancelButtonClass = "main-button" 
    confirmButtonText = "Löschen" confirmButtonClass = "error-button">
    <h2 slot="header">
        Projekt löschen?
    </h2>
    <p>
        Soll das Projekt <i>{project.projectName}</i> gelöscht werden? Alle Daten darin enthaltenen Daten inklusive der Segmentierungen werden gelöscht. Dies kann nicht rückgängig gemacht werden!
    </p>
</Modal>

<style>
    .project-container {
        border-bottom: 1px solid var(--button-color-disabled);
        padding-bottom: 5px;
    }
    .title-bar {
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    .project-name,.delete-text {
        /* Ensure that the segmentation name is cut off at some point so that it doesn't grow beyond its bounds. */
        text-overflow: ellipsis;
        white-space: nowrap;
		overflow: hidden;
    }
    .project-name-container {
        margin-left: 20px;
    }
    .delete-container {
        margin-left: 20px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 20px;
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
        margin-top: 15px;
        margin-bottom: 20px;
        font-size: 15px;
        background: var(--background-color-card-tertiary);
        color: var(--button-text-color-secondary);
    }
    .add-segmentation-button:hover {
        background: var(--background-color-card-tertiary-hover);
        color: var(--button-text-color-primary);
    }
</style>