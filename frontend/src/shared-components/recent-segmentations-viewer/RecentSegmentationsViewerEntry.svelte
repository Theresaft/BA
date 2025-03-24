<script>
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"
    import ArrowUpSymbol from "../svg/ArrowUpSymbol.svelte"
    import ClockSymbol from "../svg/ClockSymbol.svelte"
    import DownloadSymbol from "../svg/DownloadSymbol.svelte"
    import TrashSymbol from "../svg/TrashSymbol.svelte"
    import { Projects, UserSettings } from "../../stores/Store"
    import { downloadSegmentationAPI } from "../../lib/api"
    import Loading from "../../single-components/Loading.svelte"
    import Modal from "../general/Modal.svelte"
    import { SegmentationStatus } from "../../stores/Segmentation"

    import { createEventDispatcher } from "svelte"

    export let segmentationData = {}
    export let showingDetails = false
    
    let dispatch = createEventDispatcher()
    let showDownloadLoadingSymbol = false
    let showDeleteLoadingSymbol = false
    let showDeleteModal = false

    async function createDownload() {
        showDownloadLoadingSymbol = true
        const result = await downloadSegmentationAPI(getSegmentation().segmentationID, $UserSettings["defaultDownloadType"]);
        if (!result) {
            console.log("Download fehlgeschlagen.");
            return;
        }
        // get the blob and filename from the request
        const { blob, filename } = result;

        console.log("filename: " + filename)   
        
        const url = window.URL.createObjectURL(blob);
        // create an element to attach the url onto
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        // setting the download-name
        a.download = filename;
        document.body.appendChild(a);
        // simulate a click to trigger url
        a.click();
        // remove url
        window.URL.revokeObjectURL(url);
        showDownloadLoadingSymbol = false;
    }

    function showMoreButtonClicked() {
        showingDetails = !showingDetails
    }


    function getProject() {
        return $Projects.find(project => project.projectName === segmentationData.projectName)
    }
    

    function getSegmentation() {
        return getProject().segmentations.find(segmentation => segmentation.segmentationName === segmentationData.segmentationName)
    }


    function getSegmentationTime() {
        return getSegmentation().dateTime
    }

    function deleteClicked() {
        showDeleteModal = true
    }

    function deleteSegmentation() {
        dispatch("delete", segmentationData)
        showDeleteLoadingSymbol = true
    }

    function viewButtonDisabled() {
        console.log(segmentationData.segmentationID, ":", segmentationData.status)
        return segmentationData.status != SegmentationStatus["DONE"]
    }

    function getTooltip() {
        if (viewButtonDisabled()) {
            return "Erst verfügbar bei fertiger Segmentierung"
        } else {
            return "Zum Ansehen im Viewer klicken"
        }
    }
</script>

<div class="container">
    <div class="main-view">
        <div class="names-container">
            <div class="segmentation-name-container">
                <span class="segmentation-name" title="Segmentierung: {segmentationData.segmentationName}">{segmentationData.segmentationName}</span>
            </div>
            <div class="project-name-container">
                <span class="project-name" title="Projekt: {segmentationData.projectName}">{segmentationData.projectName}</span>
            </div>
        </div>
        <div class="view-button-container">
            <!-- Change segmentationData.segmentationName to segmentationData.ID-->
            <button disabled={viewButtonDisabled()} title={getTooltip()} class="view-button preview-button button" on:click={() => dispatch("view-image", { segmentationID: segmentationData.segmentationID} )}>
                Ansehen
            </button>
        </div>
        <div class="show-more-button-container">
            <button class="show-more-button" on:click={() => showMoreButtonClicked()} title={showingDetails ? "Details verbergen" : "Details anzeigen"}>
                {#if showingDetails}
                    <ArrowUpSymbol/>
                {:else}
                    <ArrowDownSymbol/>
                {/if}
            </button>
        </div>
    </div>
    {#if showingDetails}
        <div class="side-view">
            {#if !showDeleteLoadingSymbol}
                <div class="clock-symbol"><ClockSymbol/></div>
                <p class="segmentation-time"> {getSegmentationTime()}</p>
                {#if !showDownloadLoadingSymbol}
                    <button class="download-button" on:click={() => {createDownload()}}><DownloadSymbol/></button>
                {:else}
                    <div class="delete-container">
                        <Loading spinnerSizePx={15}></Loading>
                    </div>
                {/if}
                <button class="trash-button" on:click={() => deleteClicked()}><TrashSymbol sizePx={20}/></button>
            {:else}
                <div class="delete-container">
                    <Loading spinnerSizePx={15}></Loading> Segmentierung wird gelöscht...
                </div>
            {/if}
        </div>
    {/if}
</div>

<Modal bind:showModal={showDeleteModal} on:cancel={() => {}} on:confirm={() => deleteSegmentation()} cancelButtonText = "Abbrechen" cancelButtonClass = "main-button" 
    confirmButtonText="Löschen" confirmButtonClass="error-button">
    <h2 slot="header">
        Segmentierung löschen?
    </h2>
    <p>
        Soll die Segmentierung <i>{segmentationData.segmentationName}</i> gelöscht werden? Dies kann nicht rückgängig gemacht werden!
    </p>
</Modal>

<style>
    .container {
        display: flex;
        padding: 5px 10px;
        border-bottom: 1px solid var(--font-color-main);
        min-width: 300px;
        flex-direction: column;
    }
    .main-view {
        display: flex;
        gap: 8px;
        white-space: nowrap;
        align-items: center;
        flex-direction: row;
    }
    .side-view {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 20px;
    }
    .container:hover {
        background: #0001;
    }
    .clock-symbol {
        margin: auto auto;
    }
    .names-container {
        flex: 6;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .segmentation-name-container {
        flex: 1;
    }
    .project-name-container {
        flex: 1;
    }
    .segmentation-name,.project-name {
		overflow: hidden;
		text-overflow: ellipsis;
        align-self: center;
        margin: auto 0;
        min-width: 150px;
        max-width: 150px;
        display: block;
        font-size: 12px;
    }
    .project-name {
        color: var(--button-color-disabled);
    }
    .view-button-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-left: 15px;
    }

    .view-button {
        margin: 0;
        font-size: 12px;
        padding: 5px 10px;
    }

    .show-more-button-container {
        /* flex: 1; */
    }

    .show-more-button,.download-button,.trash-button, .delete-container {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: inherit;
        border-radius: 7px;
        padding: 10px;
        padding-bottom: 6px;
    }
    .delete-container {
        display: flex;
        align-items: center;
        gap: 15px;
        font-size: 12px;
    }
    .segmentation-time {
        width: 100%;
        max-width: 500px;
        font-size: 14px;
    }

</style>