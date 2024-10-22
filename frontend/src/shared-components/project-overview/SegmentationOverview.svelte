<script>
    import { createEventDispatcher } from "svelte"
    import TrashSymbol from "../../shared-components/svg/TrashSymbol.svelte"
    import ArrowUpSymbol from "../../shared-components/svg/ArrowUpSymbol.svelte"
    import ArrowDownSymbol from "../../shared-components/svg/ArrowDownSymbol.svelte"
    
    const dispatch = createEventDispatcher()
    let showingDetails = false

    export let segmentation = {}

    function deleteSegmentation() {
        // TODO Implement deletion of store variable and ensure deletion in backend!
        console.log("TODO Delete segmentation " + segmentation.segmentationName)
    }
</script>


<div class="segmentations-view">
    <!-- The title bar contains a delete button, a title (i.e., the segmentation name) and a button to unfold the content. -->
    <div class="title-bar">
        <button class="trash-button" on:click={() => deleteSegmentation()}><TrashSymbol/></button>
        <div class="project-name-container">
            <h3 class="project-name">{segmentation.segmentationName}</h3>
        </div>
        <div class="view-button-container">
            <button class="button preview-button view-button" on:click={() => {showingDetails = !showingDetails}}>Ansehen</button>
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

    {#if showingDetails}
        <div class="main-content">
            <div class="sequences-overview">
                <div class="sequence-title-wrapper">
                    <div class="sequence-title sequence-name">Sequenz</div>
                    <div class="sequence-folder-title">Ordnername</div>
                </div>
                <div class="t1-wrapper">
                    <div class="sequence-name">T1</div>
                    <div class="folder-name">{segmentation.sequenceMappings.find(obj => obj.t1).t1}</div>
                </div>
                <div class="t1-km-wrapper">
                    <div class="sequence-name">T1-KM</div>
                    <div class="folder-name">{segmentation.sequenceMappings.find(obj => obj.t1KM).t1KM}</div>
                </div>
                <div class="t2-wrapper">
                    <div class="sequence-name">T2</div>
                    <div class="folder-name">{segmentation.sequenceMappings.find(obj => obj.t2).t2}</div>
                </div>
                <div class="flair-wrapper">
                    <div class="sequence-name">Flair</div>
                    <div class="folder-name">{segmentation.sequenceMappings.find(obj => obj.flair).flair}</div>
                </div>
            </div>

            <div class="other-info">
                <div class="model-wrapper">
                    <div class="model-text">Modell:</div>
                    <div>{segmentation.model}</div>
                </div>
                <div class="date-wrapper">
                    <div class="date-text">Datum:</div>
                    <div>{segmentation.date}</div>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .segmentations-view {
        display: flex;
        flex-direction: column;
        gap: 30px;
    }
    .title-bar {
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    /* TODO Define a global class for this */
    .show-more-button,.trash-button {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: inherit;
        border-radius: 7px;
        padding: 10px;
        padding-bottom: 6px;
    }
    .project-name-container {
        margin-left: 20px;
    }
    .view-button-container {
        margin: 14px 10px auto auto;
    }
    .main-content {
        display: flex;
        flex-direction: row;
        gap: 30px;
    }
    .sequences-overview {
        flex: 2;
    }
    .other-info {
        flex: 1;
    }
    .t1-wrapper,.t1-km-wrapper,.t2-wrapper,.flair-wrapper,.sequence-title-wrapper {
        display: flex;
        flex-direction: row;
        gap: 15px;
        border-bottom: 1px solid var(--font-color-main);
        padding-bottom: 3px;
        margin-bottom: 10px;
    }
    .model-wrapper {
        margin-bottom: 20px;
    }
    .sequence-title,.sequence-folder-title,.model-text,.date-text {
        font-weight: bold;
    }
    .folder-name,.sequence-folder-title {
        margin-left: auto;
    }
</style>