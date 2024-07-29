<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import icons from "../icons.js";
	import CheckSymbol from "./svg/CheckSymbol.svelte"
    import DeleteSymbol from "./svg/DeleteSymbol.svelte"
	import DoubleCheckSymbol from "./svg/DoubleCheckSymbol.svelte"
	import FolderSymbol from "./svg/FolderSymbol.svelte";
	//look at all these beautiful options
	// Buttons text, set any to "" to remove that button
	export let buttonText = "Hochladen";
	export let doneButtonText = "Fertig";
	export let doneText = "Erfolgreich hochgeladen"
	export let descriptionText = "Hochladen per Klick oder Drag-and-drop";
	// The file upload input element
	export let input = null;
	//Files from the file input and the drag zone
	export let inputFiles = [];
	//Trigger file upload
	export let trigger = () => input.click();
	//External method to get the current files at any time
	export const getFiles = () => inputFiles;
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
	
	$: {
		let inputFilesStr = inputFiles.map(obj => obj.webkitRelativePath)
		console.log("Input files:")
		console.log(inputFilesStr)

		for (let file of inputFilesStr) {
			const parts = file.split("/")
			const curFolder = parts.slice(0, parts.length - 1).join("/") + "/"
			const curFile = parts[parts.length - 1]

			if (!foldersToFilesMapping.map(obj => obj.folder).includes(curFolder)) {
				foldersToFilesMapping = [...foldersToFilesMapping, {folder: curFolder, files: [curFile]}]
			}
			else {
				const matchIndex = foldersToFilesMapping.findIndex(obj => obj.folder === curFolder)
				let files = foldersToFilesMapping[matchIndex].files
				if (!files.includes(curFile)) {
					foldersToFilesMapping[matchIndex].files = [...foldersToFilesMapping[matchIndex].files, curFile]
					console.log("Files array:", files)
				}
			}
		}

		console.log("Map:", foldersToFilesMapping)
	}
	
	$: {
		if (inputFiles.length >= maxFiles){
			maxFilesCallback(inputFiles, maxFiles);
			dispatch("change", inputFiles)
			callback(inputFiles);
		}
	}
	
	import {createEventDispatcher} from "svelte";
	
	const dispatch = createEventDispatcher();
	
	function formatBytes(a, b = 2, k = 1024) {
			let d = Math.floor(Math.log(a) / Math.log(k));
			return 0 == a
				? "0 Bytes"
				: parseFloat((a / Math.pow(k, d)).toFixed(Math.max(0, b))) +
						" " +
						["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
	}

	function inputChanged(){
		inputFiles = [...inputFiles, ...input.files]
	}

	function del(file){
		if (idx(file, inputFiles) !== null){
			inputFiles.splice(idx(file, inputFiles), 1);
			inputFiles = [...inputFiles];
			return;
		}
		return console.log(idx(file, inputFiles))
		function idx(item, arr){
			let i = arr.findIndex(i => i === item);
			if (i < 0){return null} else {return i}
		}
	}
	function openFile(file){
		window.open(URL.createObjectURL(file), "filewin");
	}
</script>
<div class="fileUploader dragzone">
	{#if inputFiles.length !== maxFiles}
	  {#if listFiles}
			<ul>
				{#each foldersToFilesMapping.slice(0, maxFiles) as {folder, files}}
					<li>
						<span class="icon">
							<!-- <span class="fileicon">{@html getIcon(file.name)}</span> -->
							<span class="folder-icon"><FolderSymbol/></span>
							<span class="delete-icon" on:click|stopPropagation={() => del({folder, files})}><DeleteSymbol/></span>
						</span>
						<span class="filename">{folder}</span>
						<span class="filesize">{formatBytes(0)}</span>
					</li>
				{/each}
			</ul>
		{/if}
		<div class="buttons">
			<button on:click={trigger} class="upload">
				{buttonText}
			</button>
			{#if doneButtonText && inputFiles.length}<button on:click={() => (doneCallback(),callback(inputFiles))}>{doneButtonText}</button>{/if}
		</div>
		{#if descriptionText}<span class="text">{descriptionText}</span>{/if}
	{:else if maxFiles > 1}
		<DoubleCheckSymbol/>
		{#if doneText}<span class="doneText" on:click={() => callback(inputFiles)}>{doneText}</span>{/if}
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
		width: 60%;
		display: flex;
		flex-direction: column;
	}
	.dragzone li {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
		padding: 3px 8px;
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
	.buttons button {
		margin: 0 5px;
		transition: all .5s ease;
		padding: .5rem 1rem;
		margin-bottom: 1rem;
		flex: 1;
		border: 1px solid #0001;
		cursor: pointer;
		color: var(--font-color-main);
		background: rgb(20, 122, 75);
		border-radius: 3px;
	}
	.buttons button:hover {
		background: rgb(72, 212, 147);
		color: rgb(20, 50, 20);
	}
</style>