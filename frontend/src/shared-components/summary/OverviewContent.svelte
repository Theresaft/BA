<script>
    import FolderSummary from "./FolderSummary.svelte";
    import ModelSelector from "./ModelSelector.svelte";
    import NameInput from "./NameInput.svelte";
    import { createEventDispatcher } from "svelte";
    import { Projects, InvalidSymbolsInNames } from "../../stores/Store";
    import { onMount, onDestroy } from "svelte";
    import Loading from "../../single-components/Loading.svelte";
    import { Segmentation } from "../../stores/Segmentation";

    const dispatch = createEventDispatcher();

    export let segmentationToAdd = new Segmentation();
    export let project;
    export let isForExistingProject = false;

    export let projectErrorText = "";
    export let segmentationErrorText = "";
    export let reloadLoadingSymbol;

    // These are references to the corresponding components
    let projectNameInput;
    let segmentationNameInput;
    let showLoadingSymbol = false;
    // Whether the user has already modified the segmentation name. If not, the segmentation's name field is kept in sync
    // with segmentationNameSuggstion.
    let modifiedSegmentationNameByUser = false;
    // All the other segmentation names in the current project
    let otherSegmentationNames = project.segmentations.map(segmentation => segmentation.segmentationName)

    $: projectName = project.projectName;
    // This listens to changes of the reloadLoadingSymbol variable. If it changes, we hide the loading symbol.
    $: reloadLoadingSymbol, (showLoadingSymbol = false);
    // Disable the project input if the project already exists or if the loading symbol is being shown.
    $: disableProjectInput = isForExistingProject || showLoadingSymbol;
    // Disable the segmentation input if the loading symbol is being shown.
    $: disableSegmentationInput = showLoadingSymbol;


    onMount(() => {
        // Set the initial scroll position to 0 on creation of this page
        window.scrollTo({ top: 0 });
        // Pre-fill the segmentation name field with a suggestion based on the current date and the chosen model
        segmentationToAdd.segmentationName = getSegmentationNameSuggestion();
        if (typeof(window) != "undefined") {
            window.addEventListener('beforeunload', handleBeforeUnload)
        }
    });

    onDestroy(() => {
        if (typeof(window) != "undefined") {
            window.removeEventListener('beforeunload', handleBeforeUnload)
        }
    })


    function handleBeforeUnload(e) {
        e.preventDefault()
        e.returnValue = ""
    }

    /**
	 * Clean the suggested segmentation name from any possibly illegal symbols and then make sure that the name is unique,
     * i.e., no other segmentation in the project has the same name.
	 */
	function getCleanedSegmentationName(suggestedSegmentationName) {
		let modifiedName = suggestedSegmentationName
		for (let invalidSymbol of InvalidSymbolsInNames) {
			modifiedName = modifiedName.replaceAll(invalidSymbol, "")
		}
		
		// It may happen that the given project name already exists. In this case, we choose an alternative name.
		let counter = 1
		let uniqueName = modifiedName

		// Keep modifying the file name until it's unique.
		while (otherSegmentationNames.includes(uniqueName)) {
			uniqueName = `${modifiedName}(${counter})`
			counter++
		}

		return uniqueName
	}

    /**
     * Given the current time and the selected model, get the current suggestion for the segmentation name.
     * More specifically, we consider the current day followed by the hour and minute.
     */
    function getSegmentationNameSuggestion() {
        const formattedDate = new Date()
        .toLocaleString("de-DE", {
            day: "2-digit",
            month: "2-digit",
            year: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        }).replaceAll(".", "_").replace(":", "_").replaceAll(" ", "").replaceAll(",", "@")
        const formattedModel = segmentationToAdd.model.replaceAll(":", "_").replaceAll("-", "_")
        const rawName = `${formattedDate}_${formattedModel}`
        return getCleanedSegmentationName(rawName);
    }

    /**
     * After all the info has been entered, before starting the segmentation, we have to check if the entered data
     * is valid, i.e., if the segmentation name and the project name (the latter of which can be changed again here)
     * are valid. This is done using the corresponding helper functions from the respective NameInputs.
     * If the input is valid, we start the segmentation by letting the parent component know that this component is done.
     */
    function validateProject() {
        // Reset the error texts
        projectErrorText = "";
        segmentationErrorText = "";

        // Call the checkSyntax function of the project name input component. If an error is returned, show the
        // error in that component.
        let projectSyntaxError = projectNameInput.checkSyntax();

        // We first assume the project name to be unique. Uniqueness is only relevant when creating a new project, as is
        // checked below.
        let projectUniqueError = "";

        if (!isForExistingProject) {
            // If the project already exists, we will obviously find the project name in the list of projects, so we have
            // to distinguish this case.
            projectUniqueError = checkProjectUniqueness();
        }

        // Check if within the current project, the segmentation name is unique.
        let segmentationSyntaxError = segmentationNameInput.checkSyntax();
        let segmentationUniqueError = checkSegmentationUniqueness();

        // If all error messages are empty, the checks have all been successful and the segmentation can be started.
        if (
            projectSyntaxError === "" &&
            projectUniqueError === "" &&
            segmentationSyntaxError === "" &&
            segmentationUniqueError === ""
        ) {
            project.segmentations.push(segmentationToAdd);
            showLoadingSymbol = true;
            dispatch("startSegmentation");
        } else {
            // There is a problem with the project name
            if (projectSyntaxError !== "" || projectUniqueError !== "") {
                // Make sure to select the correct error message
                projectErrorText =
                    projectSyntaxError !== ""
                        ? projectSyntaxError
                        : projectUniqueError;
            }

            // There is a problem with the segmentation name
            if (
                segmentationSyntaxError !== "" ||
                segmentationUniqueError !== ""
            ) {
                // Make sure to select the correct error message
                segmentationErrorText =
                    segmentationSyntaxError !== ""
                        ? segmentationSyntaxError
                        : segmentationUniqueError;
            }
        }
    }

    /**
     * Check if any of the already existing project name is the same as the currently selected one.
     * If it's not unique, return a descriptive error message, otherwise return an empty error message.
     */
    function checkProjectUniqueness() {
        if (
            $Projects
                .map((project) => project.projectName)
                .includes(projectName)
        ) {
            return `Ein Projekt mit dem Titel ${projectName} existiert bereits.`;
        } else {
            return "";
        }
    }

    /*
     * Check if within the current project, the segmentation name is unique. If not, return a descriptive
     * error message, otherwise, return an empty string.
     */
    function checkSegmentationUniqueness() {
        if (
            project.segmentations
                .map((seg) => seg.segmentationName)
                .includes(segmentationToAdd.segmentationName)
        ) {
            return `Eine Segmentierung mit dem Titel ${segmentationToAdd.segmentationName} existiert in diesem Projekt bereits.`;
        } else {
            return "";
        }
    }

    /**
     * Update the segmentation name only if the user hasn't changed the name themselves yet. If they have already changed it,
     * the name remains as it is.
     */
    function updateSegmentationName() {
        if (!modifiedSegmentationNameByUser) {
            segmentationToAdd.segmentationName = getSegmentationNameSuggestion()
        }
    }

    /**
     * When this function is called, we want to set the flag modifiedSegmentationNameByUser to true.
     */
    function updateSegmentationNameFlag() {
        modifiedSegmentationNameByUser = true
    }

    /**
     * Go back to the previous page, either the folder uploader or the segmentation selector.
     */
    function goBack() {
        dispatch("goBack");
    }
</script>

<div>
    <p class="description">Dies sind die ausgewählten DICOM-Sequenzen:</p>
    <FolderSummary sequenceMappings={segmentationToAdd.selectedSequences} />
    <ModelSelector bind:selectedModel={segmentationToAdd.model} on:change={updateSegmentationName} />

    <NameInput
        nameDescription="Name für das Projekt"
        bind:inputContent={project.projectName}
        bind:this={projectNameInput}
        bind:disabled={disableProjectInput}
        bind:errorText={projectErrorText}
    />
    <NameInput
        nameDescription="Name für die Segmentierung"
        bind:inputContent={segmentationToAdd.segmentationName}
        bind:this={segmentationNameInput}
        bind:disabled={disableSegmentationInput}
        bind:errorText={segmentationErrorText}
        on:change={updateSegmentationNameFlag}
    />

    <div class="overview-button-container">
        <button class="main-button back-button" on:click={goBack}>
            Zurück
        </button>
        <button
            class="confirm-button continue-button"
            class:hidden={showLoadingSymbol}
            on:click={() => validateProject()}
        >
            Segmentierung starten
        </button>
        {#if showLoadingSymbol}
            <div id="loading-symbol-wrapper">
                <Loading spinnerSizePx={30} borderRadiusPercent={50} />
            </div>
        {/if}
    </div>
</div>

<style>
    .description {
        margin: 20px 0;
        display: flex;
        justify-content: center;
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
