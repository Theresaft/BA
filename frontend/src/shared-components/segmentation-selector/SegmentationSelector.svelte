<script>
    import FolderListTitle from "../folder-uploader/FolderListTitle.svelte"
    import FolderListEntry from "../folder-uploader/FolderListEntry.svelte"
    import Modal from "../general/Modal.svelte"
    import { createEventDispatcher, onMount } from "svelte"
	import { Segmentation } from "../../stores/Segmentation";
    
    const dispatch = createEventDispatcher()

    export let sideCardHidden = false
    // The project to which a segmentation should be added
    export let project

	onMount(() => {
		console.log("New segmentation")
		console.log(project)
	})

    const sequences = ["T1-KM", "T1", "T2/T2*", "Flair"]
    // Only updated on button click for performance reasons
	let missingSequences = sequences
    let showConfirmModal = false
	let reloadComponents

	$: currentStatus = (missingSequences.length === 0) ? statuses.success : statuses.error
	$: allSelected = project.sequences.filter(obj => obj.selected).length === project.sequences.length

    $: statuses = {
		success: {
			title: "Auswahl erfolgreich!",
			text: "Für die Auswahl wird für jede Sequenz nun der DICOM-Ordner mit der besten Auflösung ausgewählt.",
			buttonText: "Weiter",
			buttonClass: "confirm-button"
		},
		error: {
			title: "Fehler",
			text: `Für die ${missingSequences.length === 1 ? "folgende Sequenz" : "folgenden Sequenzen"} wurde kein Ordner ausgewählt: ${formatSequences(missingSequences)}`,
			buttonText: "Schließen",
			buttonClass: "error-button"
		}
	}

	// Set the initial scroll position to 0 on creation of this page
	onMount(() => {
        window.scrollTo({top: 0})
    })

	function goBack() {
		dispatch("goBack")
	}

    /**
     * TODO This is a list of functions that should be imported by FolderUploader and SegmentationSelector, instead of having duplicate code!!
     * ############################
    */
    function selectBestResolutions() {
		// Unselect all sequences
		for (let el of project.sequences) {
			el.selected = false
		}

		// Select for each type the sequence with best resolution, for sequences with same resolution select transversal acquisition plane
		for (let seq of sequences) {
			// It's possible that sequences include the symbol "/", which means any of the options are valid. So to generalize from that, we create a list of "/"-separated
			// strings.
			const seqList = seq.split("/")
            const def = project.sequences.find(obj => seqList.includes(obj.sequence))

            const best = project.sequences.reduce((min,item) => {
                if (seqList.includes(item.sequence) && ((item.resolution < min.resolution) || (item.resolution === min.resolution && item.acquisitionPlane === "ax"))) {
                    return item
                } else return min
            }, def)

			// best may not be defined if no folder has been found for the current sequence
			if (best) {
				best.selected = true
			}
		}
		reloadComponents = !reloadComponents
	}

	
    function selectOrDeselectAll() {
		// If all checkboxes are selected, deselect them all.
		let copy = project.sequences

		if (allSelected) {
			for (let obj of copy) {
				obj.selected = false
			}
		}
		
		// If at least one checkbox is not selected, select them all.
		else {
			for (let obj of copy) {
				obj.selected = true
			}
		}

		project.sequences = copy
	}

    function confirmInput() {
		missingSequences = []

		for (const seq of sequences) {
			// It's possible that sequences include the symbol "/", which means any of the options are valid. So to generalize from that, we create a list of "/"-separated
			// strings.
			const seqList = seq.split("/")
			const index = project.sequences.findIndex(obj => seqList.includes(obj.sequence) && obj.selected)
			if (index == -1) {
				missingSequences = [...missingSequences, seq]
			}
		}

		// Show the modal with an error message if at least one sequence is missing.
		if (missingSequences.length !== 0) {
			showConfirmModal = true
		} else {
			handleModalClosed()
		}
	}

    function handleModalClosed() {
		// Only if the success modal was closed, we have to close the segmentation selector, too. This is done by the parent component.
		if (missingSequences.length === 0) {
            // TODO Handle this
			// uploadSequenceTypesAPI()
			const selectedFolders = project.sequences.filter(obj => obj.selected)
			
            // This object is a temporary store of the segmentation, but it's not added to the project yet. This is not done until
            // the user actually starts the segmentation.
            const newSegmentation = new Segmentation()
			newSegmentation.model = "nnunet-model:brainns"
			newSegmentation.selectedSequences.t1 = selectedFolders.find(obj => obj.sequence === "T1")
			newSegmentation.selectedSequences.t1km = selectedFolders.find(obj => obj.sequence === "T1-KM")
			newSegmentation.selectedSequences.t2 = selectedFolders.find(obj => ["T2", "T2*"].includes(obj.sequence))
			newSegmentation.selectedSequences.flair = selectedFolders.find(obj => obj.sequence === "Flair")
			
			dispatch("closeSegmentationSelector", newSegmentation)
		}
	}

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
   /**
    * #############################
   */
</script>

<div class="container">
    <ul>
        <FolderListTitle bind:sideCardHidden={sideCardHidden}/>
        {#each project.sequences as data}
			{#key reloadComponents}
            	<FolderListEntry bind:data={data} on:openViewer bind:sideCardHidden={sideCardHidden} isDeletable={false}/>
			{/key}
        {/each}
    </ul>

    <div class="select-all-button-wrapper">
        <p id="select-button-description">
            Schnellauswahl:
        </p>
        <button on:click={selectBestResolutions} class="select-buttons">
            Beste Auflösungen
        </button>
        <button on:click={selectOrDeselectAll} class={(allSelected ? "warning-button" : "confirm-button") + " select-buttons"}>
            {#if allSelected}
                Keins
            {:else}
                Alle
            {/if}
        </button>
    </div>

    <hr id="button-separator-line">
    <div class="button-wrapper">
		<button id="back-button" on:click={goBack}>Zurück</button>
        <button id="done-button" class="confirm-button" on:click={confirmInput}>Fertig</button>
    </div>
</div>

<!-- Modal for confirming the selected sequences. This is an error modal in case at least one sequence is missing and a confirmation modal if the
 input is correct. -->
 <Modal bind:showModal={showConfirmModal} on:confirm={handleModalClosed} confirmButtonText={currentStatus.buttonText} confirmButtonClass={currentStatus.buttonClass}>
	<h2 slot="header">
		{currentStatus.title}
	</h2>
	<p>
		{currentStatus.text}
	</p>
</Modal>

<style>
    .container {
		/* padding: 20px; */
		border-radius: 6px;
		/* border: 2px dashed rgba(202, 202, 202); */
		display: flex;
		justify-content: center;
		align-items: center;
		flex-direction: column;
		transition: background-color .3s ease;
		margin-bottom: 20px;
		padding-left: 0;
	}
	.container ul {
		width: 95%;
		display: flex;
		flex-direction: column;
		padding: 0;
	}
	.select-all-button-wrapper {
		width: 95%;
		display: flex;
		margin: 25px 0;
		flex-direction: row;
		justify-content: center;
	}
    #select-button-description {
		margin-top: 9px;
		margin-bottom: 9px;
		margin-right: 30px;
		font-weight: 600;
	}
    .select-buttons {
		max-width: 140px;
		text-align: center;
		margin-bottom: 0;
		flex: 1;
	}
    #button-separator-line {
		width: 65%;
		color: var(--font-color-main);
		margin-top: 40px;
	}
    .button-wrapper {
		width: 40%;
		display: flex;
		margin-top: 25px;
		white-space: nowrap;
		flex-direction: row;
		justify-content: center;
		gap: 30px;
	}
	#back-button {
		flex: 1;
		padding-top: 15px;
		padding-bottom: 15px;
	}
    #done-button {
		flex: 1;
        padding-top: 15px;
        padding-bottom: 15px;
    }
</style>