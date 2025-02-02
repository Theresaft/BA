<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import CheckSymbol from "../svg/CheckSymbol.svelte"
	import DoubleCheckSymbol from "../svg/DoubleCheckSymbol.svelte"
    import FolderListEntry from "./FolderListEntry.svelte"
    import FolderListTitle from "./FolderListTitle.svelte"
	import Modal from "../general/Modal.svelte"
	import { createEventDispatcher, onMount } from "svelte"
	import { ShowNoDeleteModals } from "../../stores/Store"
	import JSZip from 'jszip'
	import { uploadDicomHeadersAPI } from '../../lib/api';
	import { get } from "svelte/store"
	import { Projects } from "../../stores/Store"
    import Loading from "../../single-components/Loading.svelte";
    import { Project } from "../../stores/Project";
    import { Segmentation } from "../../stores/Segmentation";
    import { Sequence, DicomSequence, NiftiSequence } from "../../stores/Sequence";

	
	// Buttons text, set any to "" to remove that button
	export let removeAllSegmentationsText = "Alle Ordner entfernen"
	export let doneText = "Erfolgreich hochgeladen"
	// The file upload input element
	export let input = null
	export let callback = () => {}
	//Maximum files that can be uploaded
	export let maxFiles = 100000000
	//Show a list of files + icons?
	export let sideCardHidden = false
	
	
	let showSelectionErrorModal = false
	let showDeleteSegmentationsModal = false
	let showDeleteCurrentSegmentationModal = false
	// When the user clicks on the delete symbol of a segmentation folder, this variable will be set
	// to that folder name.
	let currentFolderToDelete = ""
	let noMoreDeleteModals = false

	// TODO Move this variable to the Store
	const sequences = ["T1-KM", "T1", "T2/T2*", "Flair"]
	// Only updated on button click for performance reasons
	let missingSequences = sequences
	let dispatch = createEventDispatcher()
	let classificationRunning = false
	let uploaderForm
	// Contains objects with attributes fileName as a string and data, the actual payload
	// TODO Find a better solution for a very large number of uploaded files (may exceed RAM if several GBs are uploaded)
	let filesToData = []
	let reloadComponents
	let otherProjectNames = get(Projects).map(project => project.projectName)
	// This is used to replace the upload button with a loading symbol while the uploading is happening
	let uploadingFolders = false
	let resetSequenceType = true

	// When the FolderUploader is created, we already have an "empty" object to work with.
	// sequences is a list of objects, with each element representing exactly one folder. Besides the folder name,
	// an element also contains information about the files inside the folder, the payload, and the predicted sequence. 
	// For more info, refer to the documentation in Store.js. The projectID is null for now because this is info from the database
	// we don't have access to yet. It's not until the actual sending of the project information to the backend that the projectID
	// is fetched.
	export let project = new Project()

	let projectTitleError = ""
	
	// TODO Refactor (statuses.success is unnecessary), it would be enough to have a list of missing sequences.
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

	$: anyFolderUploaded = (project.sequences.length > 0)
	$: currentStatus = (missingSequences.length === 0) ? statuses.success : statuses.error
	$: allSelected = project.sequences.filter(obj => obj.selected).length === project.sequences.length

	// Ensure that project.sequences is always sorted in ascending lexicographic order.
	$: {
		switch (project.fileType) {
			case "dicom": {
				project.sequences = project.sequences.sort((a, b) => {
					if (a.folder.toLowerCase() === b.folder.toLowerCase()) {
						return 0
					}
					else return (a.folder.toLowerCase() > b.folder.toLowerCase()) ? 1 : -1
				})
				break
			}
			case "nifti" : {
				project.sequences = project.sequences.sort((a, b) => {
					if (a.fileName.toLowerCase() === b.fileName.toLowerCase()) {
						return 0
					}
					else return (a.fileName.toLowerCase() > b.fileName.toLowerCase()) ? 1 : -1
				})
				break
			}
		}

	}


	// Set the initial scroll position to 0 on creation of this page
    onMount(() => {
        window.scrollTo({top: 0})
    })


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
	 * This function is called per file, i.e. per .dcm or .nii file, respectively, and writes the
	 * data to filesToData.
	 */
	function fileHandlerWorker() {
		self.onmessage = function(e) {
			// Get the files and set up the file reader
			const file = e.data
			const reader = new FileReaderSync()

			// Fetch the data from the file sent to this function and write it into filesToData
			const fullFileName = file.webkitRelativePath
			const parts = fullFileName.split("/")
			const fileName = parts.slice(1, parts.length).join("/")

			const data = reader.readAsText(file)

			self.postMessage({fileName: fileName, data: data})
		}
	}


	// Validate if the project name entered at the beginning is valid.
	// TODO Refactor this function because this is almost the same as the variant for the segmentation name.
	function validateProjectName(e) {
		projectTitleError = ""        

        const forbiddenSymbols = [" ", "/", "\\", ":", "*", "?", "\"", "<", ">", "|", "`"]

        if (project.projectName === "") {
            projectTitleError = "Der Name für das Projekt darf nicht leer sein."
			e.preventDefault()
        }
        // Ensure that none of the forbidden symbols are included in the project title name.
        else if (forbiddenSymbols.find(symbol => project.projectName.includes(symbol)) ) {
            projectTitleError = `Der Name für das Projekt darf keins der folgenden Zeichen enthalten: ${formatList(forbiddenSymbols)}`
			e.preventDefault()
        }
		// Ensure that the project name is unique
		else if (otherProjectNames.includes(project.projectName)) {
			projectTitleError = `Es existiert bereits ein Projekt mit dem Namen ${project.projectName}.`
			e.preventDefault()
		}
	}


	function inputChanged(e) {

		// Initialize worker code as string to pass it into blob
		const workerCode = fileHandlerWorker.toString()

		// Create a Blob with the worker code
		const blob = new Blob(['(' + workerCode + ')()'], { type: 'application/javascript' })

		// Create a URL for the Blob
		const workerURL = URL.createObjectURL(blob)

		// Create a new worker using the Blob URL
		const worker = new Worker(workerURL)

		// The global filesToData array is reset so that every call of the worker can add a new file in
		// that initially empty array.
		filesToData = []

		// Send the files separately because otherwise they may be too large to send.
		const fileArray = Array.from(e.target.files)
		for (let file of fileArray) {
			worker.postMessage(file)
		}

		// Each postMessage execution reads in one file, which is then pushed onto filesToData. The execution
		// order is FIFO, so the same order as in the for loop above. Even if that is not the case, it doesn't really matter
		// because we have a map anyway. Submit the form only when all files have been read.
		worker.onmessage = function(event) {
			filesToData.push(event.data)
			// When all files have been added to filesToData, submit the form.
			if (filesToData.length == fileArray.length) {
				uploaderForm.requestSubmit()
			}
		}

		// If the user has actually uploaded data (not cancelled the dialog), show the loading symbol.
		uploadingFolders = true
	}


	function handleSubmit() {

		let newFiles = input.files

		// Now the uploading process is done and we can remove the upload symbol again
		uploadingFolders = false

		const multipleDataTypeErrorMessage = "Ungültige Dateiauswahl: Bitte laden Sie nur DICOM- oder nur NIfTI-Dateien in einem Ordner hoch, nicht beide Formate gleichzeitig. Überprüfen Sie Ihren Ordnerinhalt und versuchen Sie es erneut."

		for (let file of newFiles) {
			const fileName = file.name
			if (fileName.endsWith(".dcm")) {
				if (project.fileType === "") {
					project.fileType = "dicom"
				} else if (project.fileType !== "dicom") {
					projectTitleError = multipleDataTypeErrorMessage
					project.fileType = ""
					return
				}
			} else if(fileName.endsWith(".nii") || fileName.endsWith(".nii.gz")){
				if (project.fileType === "") {
					project.fileType = "nifti"
				} else if (project.fileType !== "nifti") {
					projectTitleError = multipleDataTypeErrorMessage
					project.fileType = ""
					return
				}
			}
		}


		switch (project.fileType){
			case "dicom": {
				// Check for added files
				for (let file of newFiles) {
					const fullFileName = file.webkitRelativePath
					const parts = fullFileName.split("/")
					const curFolder = parts.slice(1, parts.length - 1).join("/")
					const curFile = parts[parts.length - 1]

					const cleanedFullFileName = parts.slice(1, parts.length).join("/")
					
					// Given the current file name, find the corresponding payload
					const fileData = filesToData.find(obj => obj.fileName === cleanedFullFileName).data
					file.data = fileData

					// If the current folder is not in the list, add a new entry.
					if (!project.sequences.map(obj => obj.folder).includes(curFolder)) {
						const newSequence = new DicomSequence()
						newSequence.folder = curFolder
						newSequence.fileNames = [curFile]
						newSequence.files = [file]
						newSequence.classifiedSequenceType = "-"
						project.sequences = [...project.sequences, newSequence]
					}

					// If the current folder is in the list, add the current file to the list of files in case it doesn't exist in the list
					// yet. If the file is already included, we ignore it to avoid duplicates.
					else {
						const matchIndex = project.sequences.findIndex(obj => obj.folder === curFolder)
						let files = project.sequences[matchIndex].fileNames
						if (!files.includes(curFile)) {
							project.sequences[matchIndex].fileNames = [...project.sequences[matchIndex].fileNames, curFile]
							project.sequences[matchIndex].files = [...project.sequences[matchIndex].files, file]
						}
					}
				}
				
				// Once we've gathered all sequences, add the size for the entire folder.
				for (let sequence of project.sequences) {
					sequence.sizeInBytes = sequence.files.map(file => file.size).reduce((a, b) => a + b, 0)
				}
				break
			}
			case "nifti": {
				for (let file of newFiles) {
					const fullFileName = file.webkitRelativePath
					const parts = fullFileName.split("/")
					const cleanedFullFileName = parts.slice(1, parts.length).join("/")
					// Given the current file name, find the corresponding payload
					const fileData = filesToData.find(obj => obj.fileName === cleanedFullFileName).data
					file.data = fileData

					const newSequence = new NiftiSequence()
					newSequence.fileName = cleanedFullFileName
					newSequence.file = file
					project.sequences = [...project.sequences, newSequence]
				}

				// Once we've gathered all sequences, add the size for the Nifti file.
				for (let sequence of project.sequences) {
					sequence.sizeInBytes = sequence.file ? sequence.file.size : 0
				}
				break
			}
		}

		if (project.fileType === "dicom") {
			predictDicomSequences()
			classificationRunning = true
		} else if (project.fileType === "nifti") {
			classificationRunning = true
			predictNiftiSequences()
		}
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
		project.sequences = project.sequences.filter(({folder}) => folder !== currentFolderToDelete)
		currentFolderToDelete = ""
		$ShowNoDeleteModals = noMoreDeleteModals
	}


	// ------- Deletion of all elements
	// Show a popup for the deletion of all entries
	function confirmRemoveSegmentations() {
		showDeleteSegmentationsModal = true
	}


	function handleDeleteSegmentationsModalClosed() {
		// Delete all entries by setting the project.sequences array to an empty list.
		project.sequences = []
	}


	/**
	 * Predict DICOM sequences based on classification from the backend
	 */
	async function predictDicomSequences() {
		// Add try-catch block because we're handling an HTTP request. If the request fails,
		// we want to stop showing the loading symbol in each sequence entry and just set each
		// dropdown to "-".
		const zip = new JSZip();
		
		for (let el of project.sequences) {
			let folder = zip.folder(el.folder)
			let file = el.files[0]
			folder.file(file.name, file)
		}

		zip.generateAsync({type:"blob"})
		.then(async function(content) {
			// Create new formData Object
			const formData = new FormData();
			// Add Blob to formData Object
			formData.append('dicom_data', content);
			
			// Upload the DICOM Headers to obtain classification
			const response = await uploadDicomHeadersAPI(formData);
			if (response.ok) {
				const classification = await response.json()

				// Get lists from classification results
				const t1 = classification.t1
				const t1km = classification.t1km
				const t2 = classification.t2
				const t2star = classification.t2star
				const flair = classification.flair
				const rest = classification.rest

				// Store classification results in project.sequences
				for (let el of project.sequences) {
					let folder = el.folder
					if (t1.some(item => item.path === folder)) {
						const volume_object = t1.find(item => item.path === folder)
						el.classifiedSequenceType = "T1"
						el.resolution = volume_object.resolution
						el.acquisitionPlane = volume_object.acquisition_plane
					}
					if (t1km.some(item => item.path === folder)) {
						const volume_object = t1km.find(item => item.path === folder)
						el.classifiedSequenceType = "T1-KM"
						el.resolution = volume_object.resolution
						el.acquisitionPlane = volume_object.acquisition_plane
					}
					if (t2.some(item => item.path === folder)) {
						const volume_object = t2.find(item => item.path === folder)
						el.classifiedSequenceType = "T2"
						el.resolution = volume_object.resolution
						el.acquisitionPlane = volume_object.acquisition_plane
					}
					if (t2star.some(item => item.path === folder)) {
						const volume_object = t2star.find(item => item.path === folder)
						el.classifiedSequenceType = "T2*"
						el.resolution = volume_object.resolution
						el.acquisitionPlane = volume_object.acquisition_plane
					}
					if (flair.some(item => item.path === folder)) {
						const volume_object = flair.find(item => item.path === folder)
						el.classifiedSequenceType = "Flair"
						el.resolution = volume_object.resolution
						el.acquisitionPlane = volume_object.acquisition_plane
					}
					if (rest.some(item => item.path === folder)) {
						const volume_object = rest.find(item => item.path === folder)
						el.classifiedSequenceType = "-"
						el.resolution = volume_object.resolution
						el.acquisitionPlane = volume_object.acquisition_plane
					}
				}

				selectBestResolutions(true)
				classificationRunning = false
			
			// If the classification has failed due to a network failure, an error will be output on the command line
			// and the loading symbol will be hidden.
			} else {
				console.error("DICOM classification failed")
				classificationRunning = false
				reloadComponents = !reloadComponents
				dispatch("classificationError")
			}
		})
	}


	/**
	 * Predict NIFTI sequences just based on the file name. No metadata is available here to use.
	 */
	 function predictNiftiSequences() {
		console.log("Sequences")
		// The following lists give the list indices that match with each of the four sequences.
		const flairMatches = []
		const t1Matches = []
		const t1kmMatches = []
		const t2Matches = []

		// Store the indices per sequence type. If one index corresponds to several sequence types
		// (e.g. for the name "t1t2.nii.gz"), we don't make a prediction.
		for (const [index, seq] of project.sequences.entries()) {
			if (seq.fileName.toLowerCase().includes("flair")) {
				flairMatches.push(index)
			}
			if (seq.fileName.toLowerCase().includes("t1")) {
				t1Matches.push(index)
			}
			if (seq.fileName.toLowerCase().includes("t1km") || seq.fileName.toLowerCase().includes("t1-km") || seq.fileName.toLowerCase().includes("t1_km")) {
				t1kmMatches.push(index)
			}
			if (seq.fileName.toLowerCase().includes("t2")) {
				t2Matches.push(index)
			}
		}

		for (const [index, seq] of project.sequences.entries()) {
			// Unless the file name can unambiguously be assigned to one of the sequence types, the classified sequenc
			// type is "-".
			if (flairMatches.includes(index) && !t1Matches.includes(index) && 
				!t1kmMatches.includes(index) && !t2Matches.includes(index)) {
				seq.classifiedSequenceType = "Flair"
			} 
			else if (!flairMatches.includes(index) && t1Matches.includes(index) && 
				!t1kmMatches.includes(index) && !t2Matches.includes(index)) {
				seq.classifiedSequenceType = "T1"
			}
			// This is an exception: Here we allow T1 as a string because its a substring of t1km.
			else if (!flairMatches.includes(index) &&
				t1kmMatches.includes(index) && !t2Matches.includes(index)) {
				seq.classifiedSequenceType = "T1-KM"
			}
			else if (!flairMatches.includes(index) && !t1Matches.includes(index) && 
				!t1kmMatches.includes(index) && t2Matches.includes(index)) {
				seq.classifiedSequenceType = "T2"
			}
			else {
				seq.classifiedSequenceType = "-"
			}
		}

		selectBestResolutions(true)
		classificationRunning = false
	}


	function onBestResolutionsClicked() {
		// Don't reload the sequence types
		resetSequenceType = false
		selectBestResolutions(false)
	}


	function selectBestResolutions(useClassifiedSequenceType) {
		// Unselect all sequences
		for (let el of project.sequences) {
			el.selected = false
		}

		// Select for each type the sequence with best resolution, for sequences with same resolution select transversal acquisition plane
		for (let seq of sequences) {
			// It's possible that sequences include the symbol "/", which means any of the options are valid. So to generalize from that, we create a list of "/"-separated strings.
			const seqList = seq.split("/")
            const def = project.sequences.find(obj => seqList.includes(useClassifiedSequenceType ? obj.classifiedSequenceType : obj.sequenceType))

            const best = project.sequences.reduce((min, item) => {
                if (seqList.includes(useClassifiedSequenceType ? item.classifiedSequenceType : item.sequenceType) && item.resolution &&
				 (!min.resolution || (item.resolution < min.resolution) || 
				 (item.resolution === min.resolution && item.acquisitionPlane === "ax"))) {
                    return item
                }
				else {
					return min
				}
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
			// It's possible that sequences include the symbol "/", which means any of the options are valid. So to generalize from that, we create a list of "/"-separated
			// strings.
			const seqList = seq.split("/")
			const index = project.sequences.findIndex(obj => seqList.includes(obj.sequenceType) && obj.selected)
			if (index == -1) {
				missingSequences = [...missingSequences, seq]
			}
		}

		// Show the modal with an error message if at least one sequenceType is missing.
		if (missingSequences.length !== 0) {
			showSelectionErrorModal = true
		} else {
			handleSelectionErrorModalClosed()
		}

	}


	// TODO Refactor this (name and when this is called).
	function handleSelectionErrorModalClosed() {
		// Only if the success modal was closed, we have to close the folder uploader, too. This is done by the parent component.
		if (missingSequences.length === 0) {
			const selectedFolders = project.sequences.filter(obj => obj.selected)
			
			// Upon creation of a new segmentation, this segmentation gets certain default values we can't fill in yet. But we give the
			// object all data we have.
			const newSegmentation = new Segmentation()
			newSegmentation.model = "nnunet-model:brainns"
			newSegmentation.selectedSequences.t1 = selectedFolders.find(obj => obj.sequenceType === "T1")
			newSegmentation.selectedSequences.t1km = selectedFolders.find(obj => obj.sequenceType === "T1-KM")
			newSegmentation.selectedSequences.t2 = selectedFolders.find(obj => ["T2", "T2*"].includes(obj.sequenceType))
			newSegmentation.selectedSequences.flair = selectedFolders.find(obj => obj.sequenceType === "Flair")

			dispatch("closeUploader", newSegmentation)
		}
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


	function goBack() {
        dispatch("goBack")
    }
</script>
<div class="dragzone">

	{#if !anyFolderUploaded}
		<p class="description">
			Wählen Sie zunächst einen Namen für das Projekt: Dieser kann aber auch später noch geändert werden. In einem Projekt sind alle DICOM-Ordner enthalten, die für verschiedene Segmentierungen verwendet werden können. Laden Sie danach den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch.
		</p>
	{:else}
		<p class="description">
			Die passenden DICOM-Sequenzen werden automatisch ausgewählt, in der Regel die mit der besten Auflösung. Diese Auswahl können Sie danach aber noch ändern. Es muss aber von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden, also jeweils mindestens einer von T1, T2 oder T2*, T1-KM und Flair.
		</p>
	{/if}

	{#if !anyFolderUploaded}
		<h3 class="description">Name für das Projekt:</h3>
		<input type="text" placeholder="Name für das Projekt" class="project-input" bind:value={project.projectName} disabled={uploadingFolders}>
		<!-- Hide this text completely if the error message is empty to ensure no extra space is taken up. -->
		{#if projectTitleError !== ""}
			<p class="error-text">{projectTitleError}</p>
		{/if}
	{/if}
	{#if anyFolderUploaded}
		<button class="remove-folder-button error-button" on:click={() => confirmRemoveSegmentations()}>{removeAllSegmentationsText}</button>
	{/if}
	{#if project.sequences.length !== maxFiles}
		{#if anyFolderUploaded}
			<ul>
				{#if anyFolderUploaded}
					<FolderListTitle bind:sideCardHidden={sideCardHidden}/>
				{/if}
				{#each project.sequences.slice(0, maxFiles) as data}
					{#key classificationRunning, reloadComponents}
						<FolderListEntry bind:data={data} on:openViewer on:delete={deleteEntry} bind:disabled={classificationRunning} bind:sideCardHidden={sideCardHidden} bind:fileType={project.fileType} isDeletable={true} {resetSequenceType}></FolderListEntry>
					{/key}
				{/each}
			</ul>

			{#if anyFolderUploaded}
				<div class="select-all-button-wrapper">
					<p id="select-button-description">
						Schnellauswahl:
					</p>
					<button on:click={onBestResolutionsClicked} class="select-buttons">
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
		<div class="button-wrapper" class:button-wrapper-error={projectTitleError !== ""}>
			<button id="back-button" on:click={goBack}>Zurück</button>
			{#if !anyFolderUploaded}
				<form id="upload-form" bind:this={uploaderForm} on:submit|preventDefault={handleSubmit} enctype='multipart/form-data' class:hidden={uploadingFolders}>
					<label id="upload-label" for="upload-input" class="button confirm-button upload-button" on:click={validateProjectName}>
						Hochladen
					</label>
					<input id="upload-input" type="file" bind:this={input} webkitdirectory on:change={inputChanged} multiple={maxFiles > 1}
						style="visibility:hidden;" class="button upload-button">
				</form>
				{#if uploadingFolders}
					<div id="loading-symbol-wrapper">
						<Loading spinnerSizePx={30} borderRadiusPercent={50}/>
					</div>
				{/if}
			{:else}
				<button class="confirm-button done-button" on:click={() => (confirmInput())}>Fertig</button>
			{/if}
		</div>
	{:else if maxFiles > 1}
		<DoubleCheckSymbol/>
		{#if doneText}<button class="doneText confirm-button" on:click={() => callback(project.sequences)}>{doneText}</button>{/if}
	{:else}
		<CheckSymbol/>
		{#if doneText}<span class="doneText">{doneText}</span>{/if}
	{/if}
</div>

<!-- Modal for confirming the selected sequences. This is an error modal in case at least one sequenceType is missing and a confirmation modal if the
 input is correct. -->
<Modal bind:showModal={showSelectionErrorModal} on:confirm={handleSelectionErrorModalClosed} confirmButtonText={currentStatus.buttonText} confirmButtonClass={currentStatus.buttonClass}>
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
		opacity: .5;
		font-style: italic;
		margin-top: 2rem;
	}
	.dragzone .text {
		margin-top: 20px;
		font-style: italic;
		/* color: #333; */
	}
	.button-wrapper {
		width: 50%;
		display: flex;
		padding-top: 60px;
		white-space: nowrap;
		flex-direction: row;
		justify-content: center;
		gap: 25px;
	}
	.button-wrapper.button-wrapper-error {
		padding-top: 30px;
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
	}
	.project-input {
        width: 40%;
        text-align: left;
        margin-top: 15px;
        font-size: 14px;
        padding: 6px 10px;
        border-radius: 2px;
    }
	.error-text {
        font-size: 15px;
        color: var(--button-color-error);
        /* text-shadow: white 0 0 3px; */
        width: 40%;
        /* padding: 6px 0; */
        text-align: center;
        font-weight: 600;
		margin-bottom: 20px;
    }
	#back-button {
		margin-right: 20px;
		padding-top: 15px;	
		padding-bottom: 15px;
		flex: 1;
	}
	#upload-form {
		flex: 1;
	}
	#loading-symbol-wrapper {
		flex: 1;
		display: flex;
		justify-content: center;
		padding-top: 5px;
	}
	#upload-input {
		all: unset;
		margin: 0;
		padding: 0;
		max-width: 0;
		max-height: 0;
	}
	#upload-label {
		transition: all .5s ease;
		padding: .5rem 1rem;
		margin-bottom: 1rem;
		flex: 1;
		border: 1px solid #0001;
		cursor: pointer;
		border-radius: 3px;
		background: var(--button-color-confirm);
		color: var(--button-text-color-primary);
		text-align: center;
		font-size: 14px;
		min-width: 100%;
		margin-right: 20px;
		padding-top: 15px;
		padding-bottom: 15px;
	}
	#upload-label:hover {
		color: var(--button-text-color-secondary);
		background: var(--button-color-confirm-hover);
	}
	.done-button {
		flex: 1;
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
	.hidden {
		display: none;
	}

</style>