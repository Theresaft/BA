<script>
    import CheckSymbol from "./svg/CheckSymbol.svelte"
    import DeleteSymbol from "./svg/DeleteSymbol.svelte"
	import DoubleCheckSymbol from "./svg/DoubleCheckSymbol.svelte"
	import FolderSymbol from "./svg/FolderSymbol.svelte"
	import Button from "./Button.svelte"

    export let data = {folder: "", fileNames: [], files: []}

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

    function formatBytes(a, b = 2, k = 1024) {
			let d = Math.floor(Math.log(a) / Math.log(k));
			return 0 == a
				? "0 Bytes"
				: parseFloat((a / Math.pow(k, d)).toFixed(Math.max(0, b))) +
						" " +
						["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
	}
</script>

<div class="container">
    <span class="file-container">
        <span class="icon">
            <!-- <span class="fileicon">{@html getIcon(file.name)}</span> -->
            <span class="folder-icon"><FolderSymbol/></span>
            <span class="delete-icon" on:click|stopPropagation={() => del(data)}><DeleteSymbol/></span>
        </span>
        <span class="file-name">{data.folder}</span>
    </span>
    
    <span class="preview-container">
        <div class="preview-button">
            <button class="preview-button">Ansehen</button>
        </div>
    </span>
    
    <span class="type-container">
        <select name="type" id={"type-" + data.folder.toLowerCase()} class="type-select">
            <option value="none">-</option>
            <option value="t1">T1</option>
            <option value="t1-km">T1-KM</option>
            <option value="t2">T2</option>
            <option value="flair">Flair</option>
        </select>
    </span>
    
    <span class="file-size-container">
        <span class="file-size">{formatBytes(getSizeOfFiles(data))}</span>
    </span>
    
    <span class="selection-container">
        <input type="checkbox" class="selection">
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
		/* width: 15ch; */
		text-overflow: ellipsis;
        align-self: center;
        margin-left: 20px;
		/* display: block; */
		/* font-weight: 300; */
    }
    .preview-button {
        margin: auto;
    }

    .file-container {
        flex: 32;
        display: flex;
    }
    .preview-container {
        flex: 8;
        display: flex;
    }
    .type-container {
        flex: 8;
        display: flex;
        justify-content: center;
    }
	.file-size-container {
		flex: 8;
		text-align: center;
		opacity: .6;
		font-style: italic;
	}
    .selection-container {
        flex: 1;
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
    .container svg {
        width: 15vw;
        height: 15vw;
    }
</style>