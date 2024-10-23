<script>
    import FolderSummary from "./FolderSummary.svelte"
    import ModelSelector from "./ModelSelector.svelte"
    import NameInput from "./NameInput.svelte"
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    export let segmentation
    export let projectName
    let selectedModel

    // These are references to the corresponding components
    let projectNameInput
    let segmentationNameInput

    function formatList(list) {
		// Handle the case where the array is empty
		if (list.length === 0) {
			return "";
		}
		
		// Handle the case where the array has only one item
		if (list.length === 1) {
			return list[0];
		}

        list = list.map(el => el === " " ? "Leerzeichen" : el)
		
		// Get all items except the last one
		const allExceptLast = list.slice(0, -1).join(', ');
		// Get the last item
		const lastItem = list[list.length - 1];
		
		// Combine all items with 'und' before the last one
		return `${allExceptLast} und ${lastItem}`;
	}

    /**
     * After all the info has been entered, before starting the segmentation, we have to check if the entered data
     * is valid, i.e., if the the segmentation name and the project name (the latter of which can be changed again here)
     * are valid. This is done using the corresponding helper functions from the respective NameInputs.
     * If the input is valid, we start the segmentation by letting the parent component know that this component is done.
    */
    const validateProject = () => {

        // Calling these functions will visually show an error on the screen within the NameInput components.
        let projectNameValid = projectNameInput.validateName()
        let segmentationNameValid = segmentationNameInput.validateName()

        if (projectNameValid && segmentationNameValid) {
            console.log("Starting segmentation")
            dispatch("startSegmentation")
        } else {
            console.log("Input error...")
        }
    }

    const goBackAndCleanUp = () => {
        segmentationTitleError = ""
        dispatch("goBack")
    }

</script>

<div>
    <p class="description">
        Dies sind die ausgewählten DICOM-Sequenzen:
    </p>
    <FolderSummary sequenceMappings={segmentation.sequenceMappings}/>
    <ModelSelector bind:selectedModel={segmentation.model}/>
    
    <NameInput nameDescription="Name für das Projekt" bind:inputContent={projectName} bind:this={projectNameInput}/>
    <NameInput nameDescription="Name für die Segmentierung" bind:inputContent={segmentation.segmentationName} bind:this={segmentationNameInput}/>

    <div class="overview-button-container">
        <button class="main-button back-button" on:click={goBackAndCleanUp}>
            Zurück
        </button>
        <button class="confirm-button continue-button" on:click={() => validateProject()}>
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