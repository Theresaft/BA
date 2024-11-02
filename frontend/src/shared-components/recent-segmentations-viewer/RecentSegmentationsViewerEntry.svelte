<script>
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"
    import ArrowUpSymbol from "../svg/ArrowUpSymbol.svelte"
    import ClockSymbol from "../svg/ClockSymbol.svelte"
    import DownloadSymbol from "../svg/DownloadSymbol.svelte"
    import TrashSymbol from "../svg/TrashSymbol.svelte"

    import { createEventDispatcher } from "svelte"

    let dispatch = createEventDispatcher()

    export let segmentationData = {}
    export let showingDetails = false
    // export let isHighlighted = false

    const showMoreButtonClicked = () => {
        showingDetails = !showingDetails
    }
</script>

<div class="container">
    <div class="main-view">
        <div class="segmentation-name-container">
            <span class="segmentation-name">{segmentationData.segmentationName}</span>
        </div>
        <div class="view-button-container">
            <!-- Change segmentationData.segmentationName to segmentationData.ID-->
            <button class="view-button preview-button button" on:click={() => dispatch("view-image", { id: segmentationData.id} )}>
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
            <p class="break"> {segmentationData.scheduleTime}</p>
            <button class="download-button"><DownloadSymbol/></button>
            <button class="trash-button" on:click={() => dispatch("delete", segmentationData)}><TrashSymbol/></button>
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
        gap: 20px;
    }
    .container:hover {
        background: #0001;
    }
    .clock-symbol {
        margin: auto auto;
    }
    .segmentation-name-container {
        flex: 6;
        height: 100%;
    }

    .segmentation-name {
		overflow: hidden;
		text-overflow: ellipsis;
        align-self: center;
        margin: auto 0;
        min-width: 250px;
        max-width: 250px;
        display: block;
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
    .break {
        width: 100%;
        max-width: 500px;
        /* height: 0; */
    }

</style>