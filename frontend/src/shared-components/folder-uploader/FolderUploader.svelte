<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import CheckSymbol from "../svg/CheckSymbol.svelte"
	import DoubleCheckSymbol from "../svg/DoubleCheckSymbol.svelte"
    import FolderListEntry from "./FolderListEntry.svelte";
    import FolderListTitle from "./FolderListTitle.svelte";
	import Modal from "../general/Modal.svelte";
	import {createEventDispatcher} from "svelte"
	import JSZip from 'jszip';

	
	//look at all these beautiful options
	// Buttons text, set any to "" to remove that button
	export let removeAllSegmentationsText = "Alle Ordner entfernen"
	export let uploadButtonText = "Hochladen";
	export let uploadMoreButtonText = "Mehr hochladen"
	export let doneButtonText = "Fertig";
	export let doneText = "Erfolgreich hochgeladen"
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
	
	
	let showUploadConfirmModal = false
	let showDeleteSegmentationsModal = false

	const sequences = ["T1-KM", "T1", "T2", "Flair"]
	// Only updated on button click for performance reasons
	let missingSequences = sequences
	// A mapping of folder names to the DICOM files they contain.
	// Format:
	/**
	 * {
	 * 	folder: "folder name", 
	 * 	fileNames: ["relative file name 1", "relative file name 2"], 
	 *  files: [data: ..., ...], 
	 *  sequence: "predicted sequence"
	 * }
	 * The payload can be accessed with files[index].data
	 */
	export let foldersToFilesMapping = []
	let dispatch = createEventDispatcher()
	let classification_running = false
	let uploaderForm
	// Contains objects with attributes fileName as a string and data, the actual payload
	// TODO Find a better solution for a very large number of uploaded files (may exceed RAM if several GBs are uploaded)
	let filesToData = []
	let reloadComponents
	
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

	const fileHandlerWorker = () => {
		self.onmessage = function(e) {

			// Get the files and set up the file reader
			const files = e.data
			const filesToData = []
			const reader = new FileReaderSync()
			
			// Iterate all the uploaded files, read their content, and write the objects of
			// file names and raw data into the fileToData array.
			for (let index = 0; index < files.length; index++) {
				const curFile = files.item(index)
				const fullFileName = curFile.webkitRelativePath
				const parts = fullFileName.split("/")
				const fileName = parts.slice(1, parts.length).join("/")

				const data = reader.readAsText(curFile)

				filesToData.push({fileName: fileName, data: data})
			}

			console.log("Sending postMessage")
			self.postMessage(filesToData)

		}
	}

	function inputChanged(e) {
		const workerCode = fileHandlerWorker.toString()

		// Create a Blob with the worker code
		const blob = new Blob(['(' + workerCode + ')()'], { type: 'application/javascript' })

		// Create a URL for the Blob
		const workerURL = URL.createObjectURL(blob)

		// Create a new worker using the Blob URL
		const worker = new Worker(workerURL)
		
		// postMessage is used to read the files on a separate non-blocking worker thread.
		// TODO Show loading symbol while files are being read
		worker.postMessage(e.target.files)

		// Once the reader is done, we submit the form data. This executes the function handleSubmit.
		worker.onmessage = function(event) {
			filesToData = event.data
			uploaderForm.requestSubmit()
		}
	}


	function handleSubmit() {
		let newFiles = input.files

		// Check for added files
		for (let file of newFiles) {
			const fullFileName = file.webkitRelativePath
			const parts = fullFileName.split("/")
			const curFolder = parts.slice(1, parts.length - 1).join("/") + "/"
			const curFile = parts[parts.length - 1]

			const cleanedFullFileName = parts.slice(1, parts.length).join("/")
			
			// Given the current file name, find the corresponding payload
			const fileData = filesToData.find(obj => obj.fileName === cleanedFullFileName).data
			file.data = fileData
			
			// If the current folder is not in the list, add a new entry.
			if (!foldersToFilesMapping.map(obj => obj.folder).includes(curFolder)) {
				foldersToFilesMapping = [...foldersToFilesMapping, {folder: curFolder, fileNames: [curFile], files: [file], sequence: "-"}]
			}

			// If the current folder is in the list, add the current file to the list of files in case it doesn't exist in the list
			// yet. If the file is already included, we ignore it to avoid duplicates.
			else {
				const matchIndex = foldersToFilesMapping.findIndex(obj => obj.folder === curFolder)
				let files = foldersToFilesMapping[matchIndex].fileNames
				if (!files.includes(curFile)) {
					foldersToFilesMapping[matchIndex].fileNames = [...foldersToFilesMapping[matchIndex].fileNames, curFile]
					foldersToFilesMapping[matchIndex].files = [...foldersToFilesMapping[matchIndex].files, file]
				}
			}
		}

		classification_running = true

		predictSequences()
		
		console.log("Uploaded files: ", foldersToFilesMapping)
		console.log(foldersToFilesMapping[0].files[0])
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
		const { folder } = e.detail
		const inputFolder = folder
		foldersToFilesMapping = foldersToFilesMapping.filter(({folder}) => folder !== inputFolder)
	}

	async function predictSequences() {
		const zip = new JSZip();
		
		for (let el of foldersToFilesMapping) {
			let folder = zip.folder(el.folder)
			let file = el.files[0]
			folder.file(file.name, file)
		}

		zip.generateAsync({type:"blob"})
		.then(async function(content) {
			// Neues FormData-Objekt erstellen
			const formData = new FormData();
			// Blob zum FormData-Objekt hinzufügen
			formData.append('dicom_data', content);
			const data = await uploadFiles(formData)
			
			console.log(data)

			const t1 = data.t1
			const t1km = data.t1km
			const t2 = data.t2
			const flair = data.flair
			const rest = data.rest

			for (let el of foldersToFilesMapping) {
				let folder = el.folder
				if(t1.some(item => item.path === folder)) {
					const volume_object = t1.find(item => item.path === folder)
					el.sequence = "T1"
					el.resolution = volume_object.resolution
				}
				if(t1km.some(item => item.path === folder)) {
					const volume_object = t1km.find(item => item.path === folder)
					el.sequence = "T1-KM"
					el.resolution = volume_object.resolution
				}
				if(t2.some(item => item.path === folder)) {
					const volume_object = t2.find(item => item.path === folder)
					el.sequence = "T2"
					el.resolution = volume_object.resolution
				}
				if(flair.some(item => item.path === folder)) {
					const volume_object = flair.find(item => item.path === folder)
					el.sequence = "Flair"
					el.resolution = volume_object.resolution
				}
				if(rest.some(item => item.path === folder)) {
					const volume_object = rest.find(item => item.path === folder)
					el.sequence = "-"
					el.resolution = volume_object.resolution
				}
			}
			
			selectBestResolutions()

			classification_running = false
		});
	}

	async function uploadFiles(data) {
	  let result;	
      try {
        const response = await fetch('http://127.0.0.1:5000/assign-sequence-types', {
          method: 'POST',
          body: data
        });

		if (response.ok) {
			result = await response.json();
		} else {
			console.error('Fehler bei der Anfrage:', response.statusText);
		}
      } catch (error) {
        console.log("Failed to upload file: " + error);
      }
	  return result
    }

	function selectBestResolutions() {
		let sequences = ["T1-KM", "T1", "T2", "Flair"]

		for (let el of foldersToFilesMapping) {
			el.selected = false
		}

		for (let seq of sequences) {
            const def = foldersToFilesMapping.find(obj => obj.sequence === seq)
            const best = foldersToFilesMapping.reduce((min,item) => {
                if(item.sequence === seq && item.resolution < min.resolution) {
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
		showUploadConfirmModal = true
	}

	function handleUploadConfirmModalClosed() {
		// Only if the success modal was closed, we have to close the folder uploader, too. This is done by the parent component.
		if (missingSequences.length === 0) {
			dispatch("closeUploader", foldersToFilesMapping.filter(obj => obj.selected))
		}
	}

	function handleDeleteSegmentationsModalClosed() {
		// Delete all entries by setting the foldersToFilesMapping array to an empty list.
		foldersToFilesMapping = []
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

	function confirmRemoveSegmentations() {
				
		// Show the modal with a success message if no sequences are missing and an error message if at least one
		// sequence is missing.
		showDeleteSegmentationsModal = true
	}
	
</script>
<div class="fileUploader dragzone">
	{#if foldersToFilesMapping.length > 0}
		<button class="remove-folder-button error-button" on:click={() => confirmRemoveSegmentations()}>{removeAllSegmentationsText}</button>
	{/if}
	{#if foldersToFilesMapping.length !== maxFiles}
		{#if listFiles}
			<ul>
				{#if foldersToFilesMapping.length > 0}
					<FolderListTitle/>
				{/if}
				{#each foldersToFilesMapping.slice(0, maxFiles) as data}
					{#key classification_running, reloadComponents}
						<FolderListEntry bind:data = {data} on:delete={deleteEntry} bind:disabled={classification_running}></FolderListEntry>
					{/key}
				{/each}
			</ul>

			{#if foldersToFilesMapping.length > 0}
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
			{/if}
		{/if}
		<hr id="button-separator-line">
		<div class="button-wrapper">
			<form bind:this={uploaderForm} on:submit|preventDefault={handleSubmit} enctype='multipart/form-data'>
				<label id="upload-label" for="upload-input" class="button main-button upload-button">
					{#if foldersToFilesMapping.length === 0}
						{uploadButtonText}
					{:else}
						{uploadMoreButtonText}
					{/if}
				</label>
				<input id="upload-input" type="file" bind:this={input} webkitdirectory on:change={inputChanged} multiple={maxFiles > 1}
					style="visibility:hidden;" class="button main-button upload-button">
			</form>
			{#if doneButtonText && foldersToFilesMapping.length > 0}
				<button class="confirm-button done-button" on:click={() => (confirmInput())}>{doneButtonText}</button>
			{/if}
		</div>
	{:else if maxFiles > 1}
		<DoubleCheckSymbol/>
		{#if doneText}<button class="doneText confirm-button" on:click={() => callback(foldersToFilesMapping)}>{doneText}</button>{/if}
	{:else}
		<CheckSymbol/>
		{#if doneText}<span class="doneText">{doneText}</span>{/if}
	{/if}
</div>

<Modal bind:showModal={showUploadConfirmModal} on:confirm={handleUploadConfirmModalClosed} confirmButtonText={currentStatus.buttonText} confirmButtonClass={currentStatus.buttonClass}>
	<h2 slot="header">
		{currentStatus.title}
	</h2>
	<p>
		{currentStatus.text}
	</p>
</Modal>

<Modal bind:showModal={showDeleteSegmentationsModal} on:confirm={handleDeleteSegmentationsModalClosed} confirmButtonText="Alle löschen" confirmButtonClass="error-button" cancelButtonText="Zurück">
	<h2 slot="header">
		Löschen bestätigen
	</h2>
	<p>
		Sollen wirklich alle hochgeladenen Segmentierungen gelöscht werden? Dies kann nicht rückgängig gemacht werden!
	</p>
</Modal>

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
		margin-bottom: 20px;
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
	.button-wrapper {
		width: 40%;
		display: flex;
		margin-top: 25px;
		white-space: nowrap;
		flex-direction: row;
		justify-content: center;
		gap: 50px;
	}
	.remove-folder-button {
		margin-top: 20px;
	}
	form {
		all: unset;
		margin: 0;
		padding: 0;
		flex: 1;
		display: flex;
		justify-content: center;
		/* width: 50%; */
		/* max-width: 100px; */
	}
	#upload-input {
		all: unset;
		margin: 0;
		padding: 0;
		max-width: 0;
		max-height: 0;
	}
	#upload-label {
		/* margin: 0 5px; */
		transition: all .5s ease;
		padding: .5rem 1rem;
		margin-bottom: 1rem;
		flex: 1;
		border: 1px solid #0001;
		cursor: pointer;
		border-radius: 3px;
		background: var(--button-color-main);
		color: var(--button-text-color-primary);
		text-align: center;
		font-size: 14px;
		min-width: 100%;
	}
	#upload-label:hover {
		color: var(--button-text-color-secondary);
		background: var(--button-color-main-hover);
	}
	.done-button {
		flex: 1;
		/* width: 50%; */
		/* min-width: 100px; */
		/* max-width: 100px; */
	}
	#button-separator-line {
		width: 65%;
		color: var(--font-color-main);
		margin-top: 40px;
	}
	.select-all-button-wrapper {
		width: 95%;
		display: flex;
		margin: 25px 0;
		flex-direction: row;
		justify-content: center;
		/* justify-content: right; */
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
	.text {
		margin-bottom: 20px;
	}

</style>