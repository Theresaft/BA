<script>
    import ArrowDownSymbol from "../svg/ArrowDownSymbol.svelte"

    export let segmentationData = {}
    export let showDetails = false
    export let isHighlighted = false

    const showMoreButtonClicked = () => {
        console.log("Showing details...")
        showDetails = !showDetails
    }
</script>

<div class="container">
    <div class="segmentation-name-container">
        <span class="segmentation-name">{segmentationData.segmentationName}</span>
    </div>
    <div class="view-button-container">
        <button class="view-button preview-button button">Ansehen</button>
    </div>
    <div class="show-more-button-container">
        <button class="show-more-button" on:click={() => showMoreButtonClicked()} title={showDetails ? "Details anzeigen" : "Details verbergen"}>
            <ArrowDownSymbol/>
        </button>
    </div>
</div>

<style>
    .container {
        display: flex;
        padding: 5px 10px;
        gap: 20px;
        white-space: nowrap;
        align-items: center;
        border-bottom: 1px solid var(--font-color-main);
    }
    .container:hover {
        background: #0001;
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
        max-width: 300px;
        display: block;
    }

    .view-button-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        /* flex: 1; */
    }

    .view-button {
        margin: 0;
    }

    .show-more-button-container {
        /* flex: 1; */
    }

    .show-more-button {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: inherit;
        border-radius: 7px;
        padding: 10px;
        padding-bottom: 6px;
    }

</style>