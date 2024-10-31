<script>
    import FolderSummary from "./FolderSummary.svelte"
    import ModelSelector from "./ModelSelector.svelte"
    import NameInput from "./NameInput.svelte"
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    export let segmentationToAdd
    export let project
    export let disableProjectName=false

    $: projectName = project.projectName

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
     * Get the current formatted date.
     * TODO Move this elsewhere and define a timestamp scheme.
    */
    const getFormattedDate = () => {
        let d = new Date()

        const day = d.getDate().toString().padStart(2, '0')
        const month = (d.getMonth() + 1).toString().padStart(2, '0')
        const year = d.getFullYear()
        const hours = d.getHours().toString().padStart(2, '0')
        const minutes = d.getMinutes().toString().padStart(2, '0')
        const seconds = d.getSeconds().toString().padStart(2, '0')

        return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`
    }

    /**
     * After all the info has been entered, before starting the segmentation, we have to check if the entered data
     * is valid, i.e., if the the segmentation name and the project name (the latter of which can be changed again here)
     * are valid. This is done using the corresponding helper functions from the respective NameInputs.
     * If the input is valid, we start the segmentation by letting the parent component know that this component is done.
    */
    const validateProject = () => {

        // Calling these functions will visually show an error on the screen within the NameInput components if there is
        // an error. If not, their return value is true and the check below goes to the first case.
        let projectNameValid = projectNameInput.validateName()
        let segmentationNameValid = segmentationNameInput.validateName()

        if (projectNameValid && segmentationNameValid) {
            console.log("Starting segmentation")
            // Write the current time into the segmentation, denoting the time of initialization. Also, add the segmentationToAdd
            // to the project now
            segmentationToAdd.date = getFormattedDate()
            project.segmentations.push(segmentationToAdd)
            dispatch("startSegmentation")
        } else {
            console.log("Input error...")
        }
    }

    const goBackAndCleanUp = () => {
        dispatch("goBack")
    }

</script>

<div>
    <p class="description">
        Dies sind die ausgewählten DICOM-Sequenzen:
    </p>
    <FolderSummary sequenceMappings={segmentationToAdd.sequenceMappings}/>
    <ModelSelector bind:selectedModel={segmentationToAdd.model}/>
    
    <NameInput nameDescription="Name für das Projekt" bind:inputContent={project.projectName} bind:this={projectNameInput} bind:disabled={disableProjectName}/>
    <NameInput nameDescription="Name für die Segmentierung" bind:inputContent={segmentationToAdd.segmentationName} bind:this={segmentationNameInput}/>

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