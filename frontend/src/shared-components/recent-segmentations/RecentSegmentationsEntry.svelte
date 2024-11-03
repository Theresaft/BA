<script>
    import { createEventDispatcher } from "svelte"
    import { Projects } from "../../stores/Store";
    export let segmentationData = {}
    let viewTitle = ""

    const dispatch = createEventDispatcher();

    const getStatusClass = (id) => {
        switch(id) {
            case "pending": return "--button-color-main"
            case "queueing": return "--button-color-preview"
            case "done": return "--button-color-confirm"
            case "canceled": return "--button-color-warning"
            case "error": return "--button-color-error"
            default: return ""
        }
    }

    /*
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
        */

    // $: statusId = segmentationData.segmentationStatus.id

    function getProject() {
        return $Projects.find(project => project.projectName === segmentationData.projectName)
    }

    function getSegmentation() {
        return getProject().segmentations.find(segmentation => segmentation.segmentationName === segmentationData.segmentationName)
    }

    function getSegmentationStatusId() {
        // TODO Ensure this attribute exists in the object
        // getSegmentation().segmentationStatus
        return "done"
    }

    function getSegmentationStatusDisplayName() {
        // TODO Implement
        return "Fertig"
    }

    function getSegmentationTime() {
        return getSegmentation().date
    }
</script>

<div class="container">
    <div class="names-container">
        <div class="segmentation-name-container">
            <span class="segmentation-name" title="Segmentierung: {segmentationData.segmentationName}">{segmentationData.segmentationName}</span>
        </div>
        <div class="project-name-container">
            <span class="project-name" title="Projekt: {segmentationData.projectName}">{segmentationData.projectName}</span>
        </div>
    </div>
    
    <div class="info-container">
        <!-- TODO Replace this with an SVG representation of the status -->
        <!-- TODO Implement this correctly -->
        <span class="segmentation-status" title="Status der Segmentierung" style="color: var({getStatusClass(getSegmentationStatusId())})">{getSegmentationStatusDisplayName()}</span>
        <span class="segmentation-time" title="Start der Segmentierung">{getSegmentationTime()}</span>
    </div>

    <div class="segmentation-button-container">
        <!-- TODO Implement this -->
        <button class="segmentation-button preview-button button" 
            disabled="{/*segmentationData.segmentationStatus.id !== "done"*/ ""}"
            on:click={() => dispatch('open-viewer', { id: segmentationData.id})} 
            title={viewTitle}>
                Ansehen
        </button>
    </div>
</div>

<style>
    .container {
        display: flex;
        flex-direction: row;
        gap: 20px;
        white-space: nowrap;
        align-items: center;
        border-bottom: 1px solid var(--font-color-main);
        margin-bottom: 10px;
        padding-bottom: 10px;
    }
    .names-container {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        flex: 3;
        gap: 10px;
    }
    .info-container {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 10px;
        font-size: 14px;
    }
    .segmentation-name-container {
        flex: 1;
    }
    .project-name-container {
        flex: 1;
    }
    .segmentation-name {
        overflow: hidden;
        text-overflow: ellipsis;
        align-self: center;
        display: block;
        font-size: 14px;
        font-weight: bold;
        /* Adapt the maximum size of the segmentation name depending on the screen width (keep up to date with style below) */
        @media only screen and (min-width: 1600px) {
            max-width: 250px;
        }
        @media only screen and (min-width: 1400px) and (max-width: 1599px) {
            max-width: 225px;
        }
        @media only screen and (max-width: 1399px) {
            max-width: 180px;
        }
    }
    .project-name {
        color: var(--button-color-disabled);
        align-self: center;
        display: block;
        text-overflow: ellipsis;
        font-size: 14px;
        overflow: hidden;
        /* Adapt the maximum size of the segmentation name depending on the screen width (keep up to date with style above) */
        @media only screen and (min-width: 1600px) {
            max-width: 250px;
        }
        @media only screen and (min-width: 1400px) and (max-width: 1599px) {
            max-width: 225px;
        }
        @media only screen and (max-width: 1399px) {
            max-width: 180px;
        }
    }
    .segmentation-button {
        margin: 0;
    }

</style>