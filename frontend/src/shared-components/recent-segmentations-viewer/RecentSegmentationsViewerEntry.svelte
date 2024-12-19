<script>
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"
    import ArrowUpSymbol from "../svg/ArrowUpSymbol.svelte"
    import ClockSymbol from "../svg/ClockSymbol.svelte"
    import DownloadSymbol from "../svg/DownloadSymbol.svelte"
    import TrashSymbol from "../svg/TrashSymbol.svelte"
    import { Projects } from "../../stores/Store"

    import { createEventDispatcher } from "svelte"

    export let segmentationData = {}
    export let showingDetails = false
    
    let dispatch = createEventDispatcher()


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
        return getSegmentation().date
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
            <button class="view-button preview-button button" on:click={() => dispatch("view-image", { segmentationID: segmentationData.segmentationID} )}>
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
            <div class="clock-symbol"><ClockSymbol/></div>
            <p class="segmentation-time"> {getSegmentationTime()}</p>
            <!-- TODO Implement download -->
            <button class="download-button" on:click={() => {}}><DownloadSymbol/></button>
            <button class="trash-button" on:click={() => dispatch("delete", segmentationData)}><TrashSymbol sizePx={20}/></button>
        </div>
    {/if}
</div>

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
        min-width: 250px;
        max-width: 250px;
        display: block;
        font-size: 14px;
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
    }

    .show-more-button-container {
        /* flex: 1; */
    }

    .show-more-button,.download-button,.trash-button {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: inherit;
        border-radius: 7px;
        padding: 10px;
        padding-bottom: 6px;
    }
    .segmentation-time {
        width: 100%;
        max-width: 500px;
        font-size: 14px;
    }

</style>