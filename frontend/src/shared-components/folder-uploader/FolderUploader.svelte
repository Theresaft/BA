<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import CheckSymbol from "../svg/CheckSymbol.svelte"
	import DoubleCheckSymbol from "../svg/DoubleCheckSymbol.svelte"
    import FolderListEntry from "./FolderListEntry.svelte"
    import FolderListTitle from "./FolderListTitle.svelte"
	import Modal from "../general/Modal.svelte"
	import {createEventDispatcher} from "svelte"
	import { ShowNoDeleteModals } from "../../stores/Store"
	import JSZip from 'jszip'
	import { apiStore } from '../../stores/apiStore';


	
	//look at all these beautiful options
	// Buttons text, set any to "" to remove that button
	export let removeAllSegmentationsText = "Alle Ordner entfernen"
	export let uploadButtonText = "Hochladen"
	export let uploadMoreButtonText = "Mehr hochladen"
	export let doneButtonText = "Fertig"
	export let doneText = "Erfolgreich hochgeladen"
	// The file upload input element
	export let input = null
	export let callback = () => {}
	//Maximum files that can be uploaded
	export let maxFiles = 100000000
	//Show a list of files + icons?
	export let listFiles = true 
	
	
	let showUploadConfirmModal = false
	let showDeleteSegmentationsModal = false
	let showDeleteCurrentSegmentationModal = false
	// When the user clicks on the delete symbol of a segmentation folder, this variable will be set
	// to that folder name.
	let currentFolderToDelete = ""
	let noMoreDeleteModals = false

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
	let classificationRunning = false
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

	$: anyFolderUploaded = (foldersToFilesMapping.length > 0)
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

		classificationRunning = true

		predictSequences()
		
		console.log("Uploaded files: ", foldersToFilesMapping)
		console.log(foldersToFilesMapping[0].files[0])
	}


	// ------- Deletion of one element
	// Show a popup for the deletion of a segmentation entry
	function deleteEntry(e) {

		currentFolderToDelete = e.detail.folder
		
		// If the Store variable says to not ask for confirmation, skip the modal. Otherwise, 
		// show the modal as normal with a non-checked checkbox.
		if ($ShowNoDeleteModals) {
			noMoreDeleteModals = true
			handleDeleteCurrentSegmentationModalClosed()
		} else {
			noMoreDeleteModals = false
			showDeleteCurrentSegmentationModal = true
		}
	}

	// No matter what the user clicked when cancelling the deletion of an element, the input will be ignored.
	function handleDeleteCurrentSegmentationModalCanceled() {
		noMoreDeleteModals = false
	}

	// The previously set currentFolderToDelete variable contains the folder that should be deleted
	function handleDeleteCurrentSegmentationModalClosed() {
		foldersToFilesMapping = foldersToFilesMapping.filter(({folder}) => folder !== currentFolderToDelete)
		currentFolderToDelete = ""
		$ShowNoDeleteModals = noMoreDeleteModals
	}


	// ------- Deletion of all elements
	// Show a popup for the deletion of all entries
	function confirmRemoveSegmentations() {
		showDeleteSegmentationsModal = true
	}

	function handleDeleteSegmentationsModalClosed() {
		// Delete all entries by setting the foldersToFilesMapping array to an empty list.
		foldersToFilesMapping = []
	}


	// ------- Sequence predictions
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
			
			// Trigger the store to upload the files
			await apiStore.uploadDicomHeaders(formData);

			// Wait until the store's `uploadedFiles` is updated
			let data;
			$: data = $apiStore.classifications;
			
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
					el.acquisitionPlane = volume_object.acquisition_plane
				}
				if(t1km.some(item => item.path === folder)) {
					const volume_object = t1km.find(item => item.path === folder)
					el.sequence = "T1-KM"
					el.resolution = volume_object.resolution
					el.acquisitionPlane = volume_object.acquisition_plane
				}
				if(t2.some(item => item.path === folder)) {
					const volume_object = t2.find(item => item.path === folder)
					el.sequence = "T2"
					el.resolution = volume_object.resolution
					el.acquisitionPlane = volume_object.acquisition_plane
				}
				if(flair.some(item => item.path === folder)) {
					const volume_object = flair.find(item => item.path === folder)
					el.sequence = "Flair"
					el.resolution = volume_object.resolution
					el.acquisitionPlane = volume_object.acquisition_plane
				}
				if(rest.some(item => item.path === folder)) {
					const volume_object = rest.find(item => item.path === folder)
					el.sequence = "-"
					el.resolution = volume_object.resolution
					el.acquisitionPlane = volume_object.acquisition_plane
				}
			}
			
			selectBestResolutions()

			classificationRunning = false
		});
	}


	function selectBestResolutions() {
		let sequences = ["T1-KM", "T1", "T2", "Flair"]

		for (let el of foldersToFilesMapping) {
			el.selected = false
		}

		for (let seq of sequences) {
            const def = foldersToFilesMapping.find(obj => obj.sequence === seq)
            const best = foldersToFilesMapping.reduce((min,item) => {
                if(item.sequence === seq && ((item.resolution < min.resolution) || (item.resolution === min.resolution && item.acquisitionPlane === "cor"))) {
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
	{#if anyFolderUploaded}
		<button class="remove-folder-button error-button" on:click={() => confirmRemoveSegmentations()}>{removeAllSegmentationsText}</button>
	{/if}
	{#if foldersToFilesMapping.length !== maxFiles}
		{#if listFiles}
			<ul>
				{#if anyFolderUploaded}
					<FolderListTitle/>
				{/if}
				{#each foldersToFilesMapping.slice(0, maxFiles) as data}
					{#key classificationRunning, reloadComponents}
						<FolderListEntry bind:data = {data} on:openViewer on:delete={deleteEntry} bind:disabled={classificationRunning}></FolderListEntry>
					{/key}
				{/each}
			</ul>

			{#if anyFolderUploaded}
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
		{#if anyFolderUploaded}
			<hr id="button-separator-line">
		{/if}
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
			{#if doneButtonText && anyFolderUploaded}
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

<!-- Modal for confirming the selected sequences. This is an error modal in case at least one sequence is missing and a confirmation modal if the
 input is correct. -->
<Modal bind:showModal={showUploadConfirmModal} on:confirm={handleUploadConfirmModalClosed} confirmButtonText={currentStatus.buttonText} confirmButtonClass={currentStatus.buttonClass}>
	<h2 slot="header">
		{currentStatus.title}
	</h2>
	<p>
		{currentStatus.text}
	</p>
</Modal>

<!-- Modal for confirming the deletion of a single entry. This modal can be suppressed by clicking the corresponding checkbox in the modal. -->
<Modal bind:showModal={showDeleteCurrentSegmentationModal} on:confirm={handleDeleteCurrentSegmentationModalClosed} on:cancel={handleDeleteCurrentSegmentationModalCanceled} confirmButtonText="Löschen" confirmButtonClass="error-button" cancelButtonText="Abbrechen">
	<h2 slot="header">
		Löschen bestätigen
	</h2>
	<p>
		Soll der ausgewählte Segmentierungs-Ordner "{currentFolderToDelete}" wirklich gelöscht werden?
	</p>
	<div slot="footer">
		<label class="no-select" for="confirm-no-more-delete-modals" on:click={() => {noMoreDeleteModals = !noMoreDeleteModals}}>
			<input type="checkbox" id="confirm-no-more-delete-modal" name="confirm-no-more-delete-modals" bind:checked={noMoreDeleteModals} tabindex="-1">
			Diese Nachricht nicht mehr anzeigen
		
		</label>
	</div>
</Modal>

<!-- Modal for confirming the deletion of all listed entries. This modal can't be skipped. -->
<Modal bind:showModal={showDeleteSegmentationsModal} on:confirm={handleDeleteSegmentationsModalClosed} confirmButtonText="Alle löschen" confirmButtonClass="error-button" cancelButtonText="Abbrechen">
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
	.no-select {
		user-select: none;
	}

</style>