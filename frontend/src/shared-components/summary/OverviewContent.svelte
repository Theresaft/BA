<script>
    import FolderSummary from "./FolderSummary.svelte"
    import ModelSelector from "./ModelSelector.svelte"
    import NameInput from "./NameInput.svelte"
    import { createEventDispatcher } from "svelte"
    import { Projects } from "../../stores/Store"
    import { onMount } from 'svelte'
    
    const dispatch = createEventDispatcher()

    export let segmentationToAdd
    export let project
    export let isForExistingProject = false

    export let projectErrorText = ""
    export let segmentationErrorText = ""
    
    
    // These are references to the corresponding components
    let projectNameInput
    let segmentationNameInput

    $: projectName = project.projectName

    // Set the initial scroll position to 0 on creation of this page
    onMount(() => {
        window.scrollTo({top: 0})
    })


    /**
     * Get the current formatted date.
     * TODO Move this elsewhere and define a timestamp scheme.
    */
    function getFormattedDate() {
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
    function validateProject() {
        // Calling these functions will visually show an error on the screen within the NameInput components if there is
        // an error. If not, their return value is true and the check below goes to the first case.
        let projectNameValid = projectNameInput.validateName()
        // We first assume the project name to be unique. Uniqueness is only relevant when creating a new project, as is
        // checked below.
        let projectNameUnique = true

        if (!isForExistingProject) {
            // If the project already exists, we will obviously find the project name in the list of projects, so we have
            // to distinguish this case.
            projectNameUnique = isProjectNameUnique()
        }

        // Check if within the current project, the segmentation name is unique.
        let segmentationNameValid = segmentationNameInput.validateName()
        let segmentationNameUnique = isSegmentationNameUnique()


        if (projectNameValid && projectNameUnique && segmentationNameValid && segmentationNameUnique) {
            // Reset the error texts
            projectErrorText = ""
            segmentationErrorText = ""
            // Write the current time into the segmentation, denoting the time of initialization. Also, add the segmentationToAdd
            // to the project now
            segmentationToAdd.date = getFormattedDate()
            project.segmentations.push(segmentationToAdd)
            dispatch("startSegmentation")
        } else {
            // If we have found an error inside this function, we still have to update the corresponding error texts.
            if (projectNameValid && !projectNameUnique) {
                projectErrorText = `Ein Projekt mit dem Titel ${projectName} existiert bereits.`
            // If the project name is fine, reset its error text
            } else if (projectNameValid && projectNameUnique) {
                projectErrorText = ""
            }
            if (segmentationNameValid && !segmentationNameUnique) {
                segmentationErrorText = `Eine Segmentierung mit dem Titel ${segmentationToAdd.segmentationName} existiert in diesem Projekt bereits.`
            // If the segmentationName is fine, reset its error text
            } else if (segmentationNameValid && segmentationNameUnique) {
                segmentationErrorText = ""
            }
        }
    }


    /**
     * Check if any of the already existing project name is the same as the currently selected one.
     */
    function isProjectNameUnique() {
        return !$Projects.map(project => project.projectName).includes(projectName)
    }


    /* 
     * Check if within the current project, the segmentation name is unique.
     */
    function isSegmentationNameUnique() {
        return !project.segmentations.map(seg => seg.segmentationName).includes(segmentationToAdd.segmentationName)
    }


    /**
     * Go back to the previous page, either the folder uploader or the segmentation selector.
     */
    function goBack() {
        dispatch("goBack")
    }

</script>

<div>
    <p class="description">
        Dies sind die ausgewählten DICOM-Sequenzen:
    </p>
    <FolderSummary sequenceMappings={segmentationToAdd.sequenceMappings}/>
    <ModelSelector bind:selectedModel={segmentationToAdd.model}/>
    
    <NameInput nameDescription="Name für das Projekt" bind:inputContent={project.projectName} bind:this={projectNameInput} bind:disabled={isForExistingProject} bind:errorText={projectErrorText}/>
    <NameInput nameDescription="Name für die Segmentierung" bind:inputContent={segmentationToAdd.segmentationName} bind:this={segmentationNameInput} bind:errorText={segmentationErrorText}/>

    <div class="overview-button-container">
        <button class="main-button back-button" on:click={goBack}>
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