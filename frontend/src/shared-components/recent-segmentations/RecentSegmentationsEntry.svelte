<script>
    import { createEventDispatcher } from "svelte"
    import { Projects } from "../../stores/Store";

    export let segmentation
    let viewTitle = ""

    const dispatch = createEventDispatcher();

    // Reactive statement to update the status
    let updatedSegmentation
    let currentStatus
    $: {
        // Flatten all segmentations from all projects and find the relevant one
        updatedSegmentation = $Projects
            .flatMap(project => project.segmentations)
            .find(seg => seg.segmentationID === segmentation.segmentationID);

        currentStatus = updatedSegmentation.status ? updatedSegmentation.status.displayName : "Status unbekannt";
    }

    // Reactive statement for formatted dateTime. Add leading zeros for a consistent format and layout.
    $: segmentationTime = updatedSegmentation?.dateTime 
        ? new Date(updatedSegmentation.dateTime)
            .toLocaleString(
                "de-DE", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            )
            .replace(",", "") 
        : "-";

    function getStatusClass(id) {
        switch(id) {
            case "UPLOADING": return "--button-color-main"
            case "QUEUEING": return "--button-color-warning"
            case "PREPROCESSING": return "--button-color-bright-blue"
            case "PREDICTING": return "--button-color-bright-green"
            case "DONE": return "--button-color-confirm"
            case "ERROR": return "--button-color-error"
            default: return ""
        }
    }

</script>

<div class="container">
    <div class="names-container">
        <div class="segmentation-name-container">
            <span class="segmentation-name" title="Segmentierung: {segmentation.segmentationName}">{segmentation.segmentationName}</span>
        </div>
        <div class="project-name-container">
            <span class="project-name" title="Projekt: {segmentation.projectName}">{segmentation.projectName}</span>
        </div>
    </div>
    
    <div class="info-container">
        <!-- TODO Replace this with an SVG representation of the status -->
        <!-- TODO Implement this correctly -->
        <span class="segmentation-status" title="Status der Segmentierung" style="color: var({getStatusClass(updatedSegmentation.status.id)})">{currentStatus}</span>
        <span class="segmentation-time" title="Start der Segmentierung">{segmentationTime}</span>
    </div>

    <div class="segmentation-button-container">
        <!-- TODO Implement this -->
        <button class="segmentation-button preview-button button" 
            disabled="{/*segmentationData.segmentationStatus.id !== "done"*/ ""}"
            on:click={() => dispatch('open-viewer', { id: segmentation.id})} 
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
        border-bottom: 1px solid var(--button-color-disabled);
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
        min-width: 115px;
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