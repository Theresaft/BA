<!-- A file/folder upload component that is largely taken from https://svelte.dev/repl/6b9c9445c9b74c62aca65200cde857e2?version=3.48.0
 and adapted for this usecase. -->
 <script>
	import icons from "../icons.js";
	import CheckSymbol from "./svg/CheckSymbol.svelte"
    import DeleteSymbol from "./svg/DeleteSymbol.svelte"
	import DoubleCheckSymbol from "./svg/DoubleCheckSymbol.svelte"
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
	export let dragZoneFiles = [];
	//Trigger file upload
	export let trigger = () => input.click();
	//External method to get the current files at any time
	export const getFiles = () => files;
	// Called when maxuploads is reached or the done button is clicked
	export let callback = () => {};
	//Called when the "Done" button is clicked
	export let doneCallback = () => {};
	// Drag zone element
	export let dragZone = null;
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
			const folders = foldersToFilesMapping.map(obj => obj.folder)

			if (!folders.includes(curFolder)) {
				console.log("Cur folder:", curFolder)
				console.log("Folders:", folders)
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
	$: files = [...inputFiles, ...dragZoneFiles];
	$: {
		if (files.length >= maxFiles){
			maxFilesCallback(files, maxFiles);
			dispatch("change", files)
			callback(files);
		}
	}
	
	import {createEventDispatcher} from "svelte";
	
	const dispatch = createEventDispatcher();
	
	function dragover(e){
		e.preventDefault();
		dispatch("dragover", e);
	}
	function dragenter(e){
		e.preventDefault();
		dragZone.classList.add("dragging");
		dispatch("dragenter", e);
	}
	function dragleave(e){
		e.preventDefault();
		dragZone.classList.remove("dragging");
		dispatch("dragleave", e);
	}
	function drop(e){
		e.preventDefault();
		dragZone.classList.remove("dragging");
		dragZoneFiles.push(...[...e.dataTransfer.items].filter(i => {
			console.log(i.kind)
			return true
		}).map(i => i.getAsFile()))
		dragZoneFiles = [...dragZoneFiles];
		dispatch("drop", e);
		dispatch("change", files)
	}
	function formatBytes(a, b = 2, k = 1024) {
			let d = Math.floor(Math.log(a) / Math.log(k));
			return 0 == a
				? "0 Bytes"
				: parseFloat((a / Math.pow(k, d)).toFixed(Math.max(0, b))) +
						" " +
						["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
	}
	function getIcon(filename){
		if (!filename){return icons.default}
		return Object.entries(icons).find(
			i => i[0]
				.split(",")
				.includes(filename.split(".").slice(-1)[0])
		)?.[1] || icons.default;
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
		if (idx(file, dragZoneFiles) !== null){
			dragZoneFiles.splice(idx(file, dragZoneFiles), 1);
			dragZoneFiles = [...dragZoneFiles];
			return;
		}
		return console.log(idx(file, inputFiles), idx(file, dragZoneFiles))
		function idx(item, arr){
			let i = arr.findIndex(i => i === item);
			if (i < 0){return null} else {return i}
		}
	}
	function openFile(file){
		window.open(URL.createObjectURL(file), "filewin");
	}
</script>
<div bind:this={dragZone} on:dragover={dragover} on:drop={drop} on:dragenter={dragenter} on:dragleave={dragleave} class="fileUploader dragzone">
	{#if files.length !== maxFiles}
	  {#if listFiles}
			<ul>
				{#each files.slice(0, maxFiles) as file}
					<li>
						<span class="icon">
							<span class="fileicon">{@html getIcon(file.name)}</span>
							<span class="deleteicon" on:click|stopPropagation={() => del(file)}><DeleteSymbol/></span>
						</span>
						<span class="filename">{file.webkitRelativePath}</span>
						<span class="filesize">{formatBytes(file.size)}</span>
					</li>
				{/each}
			</ul>
		{/if}
		<div class="buttons">
			<button on:click={trigger} class="upload">
				{buttonText}
			</button>
			{#if doneButtonText && files.length}<button on:click={() => (doneCallback(),callback(files))}>{doneButtonText}</button>{/if}
		</div>
		{#if descriptionText}<span class="text">{descriptionText}</span>{/if}
	{:else if maxFiles > 1}
		<DoubleCheckSymbol/>
		{#if doneText}<span class="doneText" on:click={() => callback(files)}>{doneText}</span>{/if}
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
	border: 1px solid var(--text-color-main);
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
	.dragzone li .icon{
		width: 20px;
		margin-right: 10px;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	.dragzone li .icon :global(svg){
		width: 20px;
		/* color: #333; */
	}
	.deleteicon {
		display: none;
	}
	.dragzone li:hover .fileicon {
		display: none;
	}
	.dragzone li:hover .deleteicon {
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
		transition: background-color .2s ease;
		padding: .5rem 1rem;
		margin-bottom: 1rem;
		flex: 1;
		border: 1px solid #0001;
		cursor: pointer;
		color: rgb(12, 22, 49);
		background: rgb(42, 192, 122);
	}
	.buttons button:hover {
		background: #0001;
	}
</style>