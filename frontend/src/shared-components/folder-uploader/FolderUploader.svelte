<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import CheckSymbol from "../svg/CheckSymbol.svelte"
	import DoubleCheckSymbol from "../svg/DoubleCheckSymbol.svelte"
    import FolderListEntry from "./FolderListEntry.svelte";
    import FolderListTitle from "./FolderListTitle.svelte";
	import Modal from "../general/Modal.svelte";
	import {createEventDispatcher} from "svelte"

	
	//look at all these beautiful options
	// Buttons text, set any to "" to remove that button
	export let uploadButtonText = "Hochladen";
	export let uploadMoreButtonText = "Mehr hochladen"
	export let doneButtonText = "Fertig";
	export let doneText = "Erfolgreich hochgeladen"
	export let descriptionText = "Hochladen per Klick oder Drag-and-drop";
	// The file upload input element
	export let input = null;
	//Files from the file input and the drag zone
	// export let inputFiles = [];
	//Trigger file upload
	export let trigger = () => input.click();
	//External method to get the current files at any time
	// export const getFiles = () => inputFiles;
	// Called when maxuploads is reached or the done button is clicked
	export let callback = () => {};
	//Called when the "Done" button is clicked
	export let doneCallback = () => {};
	//Maximum files that can be uploaded
	export let maxFiles = 1000000;
	// When the maximum files are uploaded
	export let maxFilesCallback = () => {};
	//Show a list of files + icons?
	export let listFiles = true
	export let uploaderDone = false
	
	
	let showModal = false
	const sequences = ["T1-KM", "T1", "T2", "Flair"]
	// Only updated on button click for performance reasons
	let missingSequences = sequences
	// A mapping of folder names to the DICOM files they contain.
	export let foldersToFilesMapping = []
	let dispatch = createEventDispatcher()
	
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

	$: currentStatus = (missingSequences.length === 0) ? statuses.success : statuses.error
	$: allSelected = foldersToFilesMapping.filter(obj => obj.selected).length === foldersToFilesMapping.length

	// Ensure that foldersToFilesMapping is always sorted in ascending lexicographic order.
	$: {
		foldersToFilesMapping = foldersToFilesMapping.sort((a, b) => {
			if (a.folder.toLowerCase() === b.folder.toLowerCase()) {
				return 0
			}
			else return (a.folder.toLowerCase() > b.folder.toLowerCase()) ? 1 : -1
		})
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

	function inputChanged() {
		let newFiles = input.files

		// Check for added files
		for (let file of newFiles) {
			const fullFileName = file.webkitRelativePath
			const parts = fullFileName.split("/")
			const curFolder = parts.slice(0, parts.length - 1).join("/") + "/"
			const curFile = parts[parts.length - 1]
			
			// If the current folder is not in the list, add a new entry.
			if (!foldersToFilesMapping.map(obj => obj.folder).includes(curFolder)) {
				const predictedSequence = predictSequence(curFolder)
				foldersToFilesMapping = [...foldersToFilesMapping, {folder: curFolder, fileNames: [curFile], files: [file], sequence: predictedSequence}]
			}
			// If the current folder is in the list, add the current file to the list of files in case it doesn't exist in the list
			// yet.
			else {
				const matchIndex = foldersToFilesMapping.findIndex(obj => obj.folder === curFolder)
				let files = foldersToFilesMapping[matchIndex].fileNames
				if (!files.includes(curFile)) {
					foldersToFilesMapping[matchIndex].fileNames = [...foldersToFilesMapping[matchIndex].fileNames, curFile]
					foldersToFilesMapping[matchIndex].files = [...foldersToFilesMapping[matchIndex].files, file]
				}
			}
		}

		assignDefaultSequenceSelection(foldersToFilesMapping)
	}

	function assignDefaultSequenceSelection(foldersToFilesMapping) {
		// TODO Replace with an API request to the backend asking for the best sequences to be selected by default.
		// For now, we just select the first element of each sequence.
		let unassignedSequences = ["T1-KM", "T1", "T2", "Flair"]

		// Initialization
		for (let el of foldersToFilesMapping) {
			el.selected = false
		}

		for (let seq of unassignedSequences) {
			foldersToFilesMapping.find(obj => obj.sequence === seq).selected = true
		}
	}

	function deleteEntry(e) {
		const {folder, fileNames, files, sequence, selected} = e.detail
		const inputFolder = folder
		foldersToFilesMapping = foldersToFilesMapping.filter(({folder}) => folder !== inputFolder)
	}

	function predictSequence(folder) {
        // TODO Replace with an API request to the backend asking for the correct sequences.
        // For now, we just search the file name.
        return searchFileNameForSequence(folder)
	}

	function searchFileNameForSequence(folder) {
		const lowercase = folder.toLowerCase()
		if (lowercase.includes("t1") && lowercase.includes("km")) {
			return "T1-KM"
		} else if (lowercase.includes("t1")) {
			return "T1"
		} else if (lowercase.includes("t2")) {
			return "T2"
		} else if (lowercase.includes("flair")) {
			return "Flair"
		} else {
			return "-"
		}
	}

	function confirmInput() {
		missingSequences = []

		for (const seq of sequences) {
			const index = foldersToFilesMapping.findIndex(obj => obj.sequence === seq && obj.selected)
			if (index == -1) {
				missingSequences = [...missingSequences, seq]
			}
		}

		// Show the modal with a success message if no sequences are missing and an error message if at least one
		// sequence is missing.
		showModal = true
	}

	function handleModalClosed() {
		// Only if the success modal was closed, we have to close the folder uploader, too. This is done by the parent component.
		if (missingSequences.length === 0) {
			dispatch("closeUploader", foldersToFilesMapping.filter(obj => obj.selected))
		}
	}

	function selectOrDeselectAll() {
		// If all checkboxes are selected, deselect them all.
		let copy = foldersToFilesMapping

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

		foldersToFilesMapping = copy
	}
	
</script>
<div class="fileUploader dragzone">
	{#if foldersToFilesMapping.length !== maxFiles}
		{#if listFiles}
			<ul>
				{#if foldersToFilesMapping.length > 0}
					<FolderListTitle/>
				{/if}
				{#each foldersToFilesMapping.slice(0, maxFiles) as data}
					<FolderListEntry {data} on:delete={deleteEntry}></FolderListEntry>
				{/each}
			</ul>

			{#if foldersToFilesMapping.length > 0}
				<div class="select-all-button-wrapper">
					<button on:click={selectOrDeselectAll} class={(allSelected ? "warning-button" : "confirm-button") + " select-all-button"}>
						{#if allSelected}
							Keins
						{:else}
							Alle
						{/if}
					</button>
				</div>
			{/if}
		{/if}
		<div class="buttons">
			<button on:click={trigger} class="main-button upload-button">
				{#if foldersToFilesMapping.length === 0}
					{uploadButtonText}
				{:else}
					{uploadMoreButtonText}
				{/if}
			</button>
			{#if doneButtonText && foldersToFilesMapping.length}
			<button class="confirm-button done-button" on:click={() => (confirmInput())}>{doneButtonText}</button>
			{/if}
		</div>
		{#if descriptionText}<span class="text">{descriptionText}</span>{/if}
	{:else if maxFiles > 1}
		<DoubleCheckSymbol/>
		{#if doneText}<button class="doneText confirm-button" on:click={() => callback(foldersToFilesMapping)}>{doneText}</button>{/if}
	{:else}
		<CheckSymbol/>
		{#if doneText}<span class="doneText">{doneText}</span>{/if}
	{/if}
</div>

<Modal bind:showModal on:click={handleModalClosed} buttonText={currentStatus.buttonText} buttonClass={currentStatus.buttonClass}>
	<h2 slot="header">
		{currentStatus.title}
	</h2>
	<p>
		{currentStatus.text}
	</p>
</Modal>

<input type="file" hidden bind:this={input} webkitdirectory on:change={inputChanged} multiple={maxFiles > 1}>

<style>
	.dragzone {
		/* padding: 20px; */
		border-radius: 6px;
		/* border: 2px dashed rgba(202, 202, 202); */
		display: flex;
		justify-content: center;
		align-items: center;
		flex-direction: column;
		transition: background-color .3s ease;
		margin-bottom: 40px;
		padding-left: 0;
	}
	.dragzone ul {
		width: 95%;
		display: flex;
		flex-direction: column;
		padding: 0;
	}
	.dragzone .doneText {
		font-size: 1.3rem;
		/* color: #333; */
		opacity: .5;
		/* font-weight: 300; */
		font-style: italic;
		margin-top: 2rem;
	}
	.dragzone .text {
		margin-top: 20px;
		font-style: italic;
		/* color: #333; */
	}
	.buttons {
		width: 20%;
		display: flex;
		margin-top: 20px;
		/* white-space: nowrap; */
		flex-direction: row;
	}
	.select-all-button-wrapper {
		width: 95%;
		display: flex;
		margin: 15px 0;
		flex-direction: row-reverse;
		/* justify-content: right; */
	}
	.select-all-button {
		max-width: 80px;
		text-align: center;

	}
	.text {
		margin-bottom: 20px;
	}

</style>