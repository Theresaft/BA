<script>
    import FolderSummary from "./FolderSummary.svelte"
    import ModelSelector from "./ModelSelector.svelte"
    import NameInput from "./NameInput.svelte"
    import { createEventDispatcher } from "svelte"
    import { Projects } from "../../stores/Store"
    import { onMount } from 'svelte'
    import Loading from "../../single-components/Loading.svelte"
    
    const dispatch = createEventDispatcher()

    export let segmentationToAdd
    export let project
    export let isForExistingProject = false

    export let projectErrorText = ""
    export let segmentationErrorText = ""
    
    
    // These are references to the corresponding components
    let projectNameInput
    let segmentationNameInput
    let uploadingSegmentation = false

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
        // Reset the error texts
        projectErrorText = ""
        segmentationErrorText = ""

        // Call the checkSyntax function of the project name input component. If an error is returned, show the
        // error in that component.
        let projectSyntaxError = projectNameInput.checkSyntax()

        // We first assume the project name to be unique. Uniqueness is only relevant when creating a new project, as is
        // checked below.
        let projectUniqueError = ""

        if (!isForExistingProject) {
            // If the project already exists, we will obviously find the project name in the list of projects, so we have
            // to distinguish this case.
            projectUniqueError = checkProjectUniqueness()
        }

        // Check if within the current project, the segmentation name is unique.
        let segmentationSyntaxError = segmentationNameInput.checkSyntax()
        let segmentationUniqueError = checkSegmentationUniqueness()

        // If all error messages are empty, the checks have all been successful and the segmentation can be started.
        if (projectSyntaxError === "" && projectUniqueError === "" && 
                segmentationSyntaxError === "" && segmentationUniqueError === "") {
            // Write the current time into the segmentation, denoting the time of initialization. Also, add the segmentationToAdd
            // to the project now
            // TODO Don't get the date in the frontend, but in the backend. But for now, this is fine.
            segmentationToAdd.date = getFormattedDate()
            project.segmentations.push(segmentationToAdd)
            uploadingSegmentation = true
            // Pass the info that we want to start the segmentation to the parent component
            dispatch("startSegmentation")
        } else {
            // There is a problem with the project name
            if (projectSyntaxError !== "" || projectUniqueError !== "") {
                // Make sure to select the correct error message
                projectErrorText = (projectSyntaxError !== "") ? projectSyntaxError : projectUniqueError
            }

            // There is a problem with the segmentation name
            if (segmentationSyntaxError !== "" || segmentationUniqueError !== "") {
                // Make sure to select the correct error message
                segmentationErrorText = (segmentationSyntaxError !== "") ? segmentationSyntaxError : segmentationUniqueError
            }
        }
    }


    /**
     * Check if any of the already existing project name is the same as the currently selected one.
     * If it's not unique, return a descriptive error message, otherwise return an empty error message.
     */
    function checkProjectUniqueness() {
        if ($Projects.map(project => project.projectName).includes(projectName)) {
            return `Ein Projekt mit dem Titel ${projectName} existiert bereits.`
        } else {
            return ""
        }
    }


    /* 
     * Check if within the current project, the segmentation name is unique. If not, return a descriptive
     * error message, otherwise, return an empty string.
     */
    function checkSegmentationUniqueness() {
        if (project.segmentations.map(seg => seg.segmentationName).includes(segmentationToAdd.segmentationName)) {
            return `Eine Segmentierung mit dem Titel ${projectName} existiert in diesem Projekt bereits.`
        } else {
            return ""
        }
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
        <button class="confirm-button continue-button" class:hidden={uploadingSegmentation} on:click={() => validateProject()}>
            Segmentierung starten
        </button>
        {#if uploadingSegmentation}
            <div id="loading-symbol-wrapper">
                <Loading spinnerSizePx={30} borderRadiusPercent={50}/>
            </div>
        {/if}
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
        padding-top: 1em;
        padding-bottom: 1em;
    }
    .continue-button {
        max-width: 16.5%;
        padding-top: 1em;
        padding-bottom: 1em;
    }
    #loading-symbol-wrapper {
        width: 16.5%;
        display: flex;
        justify-content: center;
    }
    .hidden {
		display: none;
	}
</style>