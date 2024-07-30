<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import icons from "../icons.js";
	import CheckSymbol from "./svg/CheckSymbol.svelte"
    import DeleteSymbol from "./svg/DeleteSymbol.svelte"
	import DoubleCheckSymbol from "./svg/DoubleCheckSymbol.svelte"
	import FolderSymbol from "./svg/FolderSymbol.svelte"
	import Button from "./Button.svelte"

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
	export let listFiles = true;

	// A mapping of folder names to the DICOM files they contain.
	let foldersToFilesMapping = []

	// Ensure that foldersToFilesMapping is always sorted in ascending lexicographic order.
	$: {
		foldersToFilesMapping = foldersToFilesMapping.sort((a, b) => {
			if (a.folder.toLowerCase() === b.folder.toLowerCase()) {
				return 0
			}
			else return (a.folder.toLowerCase() > b.folder.toLowerCase()) ? 1 : -1
		})
	}
	
	function formatBytes(a, b = 2, k = 1024) {
			let d = Math.floor(Math.log(a) / Math.log(k));
			return 0 == a
				? "0 Bytes"
				: parseFloat((a / Math.pow(k, d)).toFixed(Math.max(0, b))) +
						" " +
						["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
	}

	function inputChanged(){
		let newFiles = input.files

		// Check for added files
		for (let file of newFiles) {
			const fullFileName = file.webkitRelativePath
			const parts = fullFileName.split("/")
			const curFolder = parts.slice(0, parts.length - 1).join("/") + "/"
			const curFile = parts[parts.length - 1]
			
			// If the current folder is not in the list, add a new entry.
			if (!foldersToFilesMapping.map(obj => obj.folder).includes(curFolder)) {
				foldersToFilesMapping = [...foldersToFilesMapping, {folder: curFolder, fileNames: [curFile], files: [file]}]
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

		console.log("Map:", foldersToFilesMapping)
	}

	function del({folder, fileNames, files}) {
		const inputFolder = folder
		foldersToFilesMapping = foldersToFilesMapping.filter(({folder, _}) => folder !== inputFolder)
	}

	// For the given folder and files in it, compute the sum of the file sizes in the folder.
	function getSizeOfFiles({folder, fileNames, files}) {
		let sum = 0
		for (let file of files) {
			sum += file.size
		}
		return sum
	}
	
</script>
<div class="fileUploader dragzone">
	{#if foldersToFilesMapping.length !== maxFiles}
		{#if listFiles}
			<ul>
				{#each foldersToFilesMapping.slice(0, maxFiles) as obj}
					<li>
						<span class="icon">
							<!-- <span class="fileicon">{@html getIcon(file.name)}</span> -->
							<span class="folder-icon"><FolderSymbol/></span>
							<span class="delete-icon" on:click|stopPropagation={() => del(obj)}><DeleteSymbol/></span>
						</span>
						<span class="filename">{obj.folder}</span>
						<span class="filesize">{formatBytes(getSizeOfFiles(obj))}</span>
					</li>
				{/each}
			</ul>
		{/if}
		<div class="buttons">
			<Button on:click={trigger} type="main">
				{#if foldersToFilesMapping.length === 0}
					{uploadButtonText}
				{:else}
					{uploadMoreButtonText}
				{/if}
			</Button>
			{#if doneButtonText && foldersToFilesMapping.length}<Button type="confirm" on:click={() => (doneCallback(),callback(foldersToFilesMapping))}>{doneButtonText}</Button>{/if}
		</div>
		{#if descriptionText}<span class="text">{descriptionText}</span>{/if}
	{:else if maxFiles > 1}
		<DoubleCheckSymbol/>
		{#if doneText}<span class="doneText" on:click={() => callback(foldersToFilesMapping)}>{doneText}</span>{/if}
	{:else}
		<CheckSymbol/>
		{#if doneText}<span class="doneText">{doneText}</span>{/if}
	{/if}
</div>
<input type="file" hidden bind:this={input} webkitdirectory directory on:change={inputChanged} multiple={maxFiles > 1}>

<style>
	.dragzone {
		padding: 20px;
		border-radius: 6px;
		border: 2px dashed rgba(202, 202, 202);
		display: flex;
		justify-content: center;
		align-items: center;
		flex-direction: column;
		transition: background-color .3s ease;
		margin-bottom: 40px;
	}
	.dragzone ul {
		width: 80%;
		display: flex;
		flex-direction: column;
	}
	.dragzone li {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
		padding: 0px 8px;
		/* border-radius: 3px; */
	}
	li {
		border-bottom: 1px solid var(--font-color-main);
	}
	.dragzone li:hover {
		background: #0001;
	}
	.dragzone .filesize {
		flex: 1;
		text-align: right;
		opacity: .6;
		font-style: italic;
	}
	.dragzone li .filename {
		white-space: nowrap;
		overflow: hidden;
		/* width: 15ch; */
		text-overflow: ellipsis;
		display: block;
		/* font-weight: 300; */
	}
	.dragzone.dragging {
		background: #0662;
	}
	.dragzone svg:not(li svg) {
		width: 15vw;
		height: 15vw;
		/* color: #777; */
	}
	.dragzone li .icon {
		width: 20px;
		margin: 5px 15px 0px 15px;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	.dragzone li .icon :global(svg) {
		width: 20px;
		/* color: #333; */
	}
	.folder-icon {
		display: block;
	}
	.delete-icon {
		display: none;
	}
	.dragzone li:hover .folder-icon {
		display: none;
	}
	.dragzone li:hover .delete-icon {
		display: block;
		cursor: pointer;
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
		font-style: italic;
		/* color: #333; */
	}
	.buttons {
		width: 20%;
		display: flex;
	}
</style>