<script>
    export let segmentationData = {}
    let viewTitle = ""

    const getStatusClass = (id) => {
        switch(id) {
            case "pending": return "--button-color-main"
            case "queueing": return "--button-color-preview"
            case "done": return "--button-color-confirm"
            case "canceled": return "--button-color-warning"
            case "error": return "--button-color-error"
        }
    }

    $: {
        if (statusId === "done") {
            // TODO Supposed to be in tab "viewer"?
            viewTitle = "Segmentierung im Tab 'Viewer' ansehen"
        } else if (statusId === "pending" || statusId === "queueing") {
            viewTitle = "Warten auf Segmentierung..."
        } else {
            viewTitle = "Segmentierung abgebrochen/fehlgeschlagen"
        }
    }

    $: statusId = segmentationData.segmentationStatus.id
</script>

<div class="container">
    <div class="segmentation-name-container">
        <span class="segmentation-name">{segmentationData.segmentationName}</span>
    </div>
    <div class="segmentation-status-container">
        <!-- TODO Replace this with an SVG representation of the status -->
        <span class="segmentation-status" style="color: var({getStatusClass(segmentationData.segmentationStatus.id)})">{segmentationData.segmentationStatus.displayName}</span>
    </div>
    <div class="segmentation-button-container">
        <button class="segmentation-button preview-button button" disabled="{segmentationData.segmentationStatus.id !== "done"}"
            on:click={() => console.log("Clicked preview button")} title={viewTitle}>Ansehen</button>
    </div>
</div>

<style>
    .container {
        display: flex;
        padding: 15px;
        gap: 20px;
        white-space: nowrap;
        align-items: center;
    }

    .segmentation-name-container {
        flex: 1;
    }

    .segmentation-name {
		overflow: hidden;
		text-overflow: ellipsis;
        align-self: center;
        max-width: 300px;
        display: block;
    }

    .segmentation-status-container {
        /* flex: 1; */
    }

    .segmentation-status {
    }

    .segmentation-button-container {
    }

    .segmentation-button {
        margin: 0;
    }

</style>