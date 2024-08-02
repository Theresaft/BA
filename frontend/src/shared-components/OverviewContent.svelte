<script>
    import FolderSummary from "./FolderSummary.svelte";
    import ModelSelector from "./ModelSelector.svelte";
    import SegmentationNameInput from "./SegmentationNameInput.svelte";
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    export let selectedData = []
    let segmentationTitle = ""
    let segmentationTitleError = ""

    function formatSequences(sequence) {
		// Handle the case where the array is empty
		if (sequence.length === 0) {
			return "";
		}
		
		// Handle the case where the array has only one item
		if (sequence.length === 1) {
			return sequence[0];
		}
		
		// Get all items except the last one
		const allExceptLast = sequence.slice(0, -1).join(', ');
		// Get the last item
		const lastItem = sequence[sequence.length - 1];
		
		// Combine all items with 'und' before the last one
		return `${allExceptLast} und ${lastItem}`;
	}

    const validateSegmentationName = () => {

        segmentationTitleError = ""
        
        const forbiddenSymbols = [" ", "/", "\\", ":", "*", "?", "\"", "<", ">", "|", "`"]

        if (segmentationTitle === "") {
            segmentationTitleError = "Der Name für die Segmentierung darf nicht leer sein."
        }
        // Ensure that none of the forbidden symbols are included in the segmentation title name.
        else if (forbiddenSymbols.find(symbol => segmentationTitle.includes(symbol)) ) {
            segmentationTitleError = `Der Name für die Segmentierung darf keins der folgenden Zeichen enthalten:${formatSequences(forbiddenSymbols)}`
        }

        else {
            dispatch("startSegmentation", segmentationTitle)
        }
    }

    const goBackAndCleanUp = () => {
        segmentationTitleError = ""
        dispatch("goBack")
    }

    $: {
        console.log("Segmentation title:", segmentationTitle)
    }

</script>

<div>
    <p class="description">
        Dies sind die ausgewählten DICOM-Sequenzen:
    </p>
    <FolderSummary data={selectedData}/>
    <ModelSelector/>
    <SegmentationNameInput bind:segmentationTitle={segmentationTitle} bind:segmentationTitleError={segmentationTitleError}/>
    <div class="overview-button-container">
        <button class="main-button back-button" on:click={goBackAndCleanUp}>
            Zurück
        </button>
        <button class="confirm-button continue-button" on:click={() => validateSegmentationName()}>
            Segmentierung starten
        </button>
    </div>
</div>

<style>
    .description {
        margin: 20px 0;
    }
    .overview-button-container {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .back-button {
        max-width: 16.5%;
    }
    .continue-button {
        max-width: 16.5%;
    }
</style>