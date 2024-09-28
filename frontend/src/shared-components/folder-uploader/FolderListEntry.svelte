<script>
    import Loading from "../../single-components/Loading.svelte";
    import DeleteSymbol from "../svg/DeleteSymbol.svelte"
	import FolderSymbol from "../svg/FolderSymbol.svelte"
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()


    export let data = {folder: "", fileNames: [], files: [], sequence: "-", selected: false}
    export let disabled = false

	// For the given folder and files in it, compute the sum of the file sizes in the folder.
	function getSizeOfFiles({files}) {
		let sum = 0
		for (let file of files) {
			sum += file.size
		}
		return sum
	}

    function formatBytes(a, b = 2, k = 1024) {
			let d = Math.floor(Math.log(a) / Math.log(k));
			return 0 == a
				? "0 Bytes"
				: parseFloat((a / Math.pow(k, d)).toFixed(Math.max(0, b))) +
						" " +
						["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
	}

    function getId(data) {
        return `type-${data.folder.toLowerCase()}`
    }


</script>

<div class="container">
    <span class="file-container">
        <span class="icon">
            <!-- <span class="fileicon">{@html getIcon(file.name)}</span> -->
            <span class="folder-icon"><FolderSymbol/></span>
            <span class="delete-icon" on:click={() => dispatch("delete", data)}><DeleteSymbol/></span>
        </span>
        <span class="file-name">{data.folder}</span>
    </span>
    
    <span class="preview-container">
        <div class="preview-button">
            <button class="preview-button" on:click={() => dispatch("openViewer", data)}>Ansehen</button>
        </div>
    </span>
    
    <span class="type-container">

        {#if disabled}
            <Loading></Loading>
        {:else}
            <select name="type" id={getId(data)} bind:value={data.sequence} class="type-select" disabled={disabled}>
                <option value="-">-</option>
                <option value="T1">T1</option>
                <option value="T1-KM">T1-KM</option>
                <option value="T2">T2</option>
                <option value="Flair">Flair</option>
            </select>
        {/if}
    </span>
    
    <span class="file-size-container">
        <span class="file-size">{formatBytes(getSizeOfFiles(data))}</span>
    </span>
    
    <span class="selection-container">
        <input type="checkbox" class="selection" bind:checked={data.selected} disabled={disabled}>
    </span>
</div>

<style>
    .container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
        justify-content: center;
		padding: 0px 8px;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
	}
	.container:hover {
		background: #0001;
	}
    .type-select {
        /* all:unset; */
        width: 50%;
        text-align: center;
    }
    .icon {
        width: 17px;
        margin: 5px 15px 0px 15px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .file-name {
        white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
        align-self: center;
        margin-left: 20px;
        max-width: 400px;
        font-size: 15px;
    }
    .preview-button {
        margin: auto;
    }

    .file-container {
        flex: 16;
        display: flex;
    }
    .preview-container {
        flex: 4;
        display: flex;
    }
    .type-container {
        flex: 4;
        display: flex;
        justify-content: center;
    }
	.file-size-container {
		flex: 4;
		text-align: center;
		opacity: .6;
		font-style: italic;
	}
    .file-size {
        user-select: none;
    }
    .selection-container {
        flex: 2;
        display: flex;
        justify-content: center;
    }
    .selection {
        /* Double-sized Checkboxes */
        --scale: 1.5;
        -ms-transform: scale(var(--scale)); /* IE */
        -moz-transform: scale(var(--scale)); /* FF */
        -webkit-transform: scale(var(--scale)); /* Safari and Chrome */
        -o-transform: scale(var(--scale)); /* Opera */
        transform: scale(var(--scale));
        align-self: center;
        accent-color: var(--button-color-confirm);
    }
	.folder-icon {
		display: block;
	}
	.delete-icon {
		display: none;
	}
	.container:hover .folder-icon {
		display: none;
	}
	.container:hover .delete-icon {
		display: block;
		cursor: pointer;
	}
</style>