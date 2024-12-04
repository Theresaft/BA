<script>
    import Loading from "../../single-components/Loading.svelte"
	import FolderSymbol from "../svg/FolderSymbol.svelte"
    import TrashSymbol from "../svg/TrashSymbol.svelte"
    import { createEventDispatcher, onMount } from "svelte"
    
    const dispatch = createEventDispatcher()


    export let data
    export let disabled = false
    export let sideCardHidden = false
    export let isDeletable = true
    // This indicates whether the sequenceType property should be read from the classifiedSequenceType. This is the case when the component
    // is loaded for the first time. If the component already exists, but just has to be destroyed temporarily to create it again right after that,
    // we don't want to reset the sequence type.
    export let resetSequenceType = true

    onMount(() => {
        // When a classification of the sequences takes place, assign the classified type.
        if (resetSequenceType) {
            console.log("Resetting sequence type")
            data.sequenceType = data.classifiedSequenceType
        }
    })

	// For the given folder and files in it, compute the sum of the file sizes in the folder.
	function getSizeOfFiles({files}) {
		let sum = 0
		for (let file of files) {
			sum += file.size
		}
		return sum
	}

    // For the given number of bytes a, format this number with the largest unit possible and with exactly b number of displayed decimal places.
    function formatBytes(a, b = 2, k = 1024) {

        let d = Math.floor(Math.log(a) / Math.log(k));
        return 0 == a
            ? "0 Bytes"
            : (a / Math.pow(k, d)).toFixed(Math.max(0, b)) +
                    " " +
                    ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
	}

    function getId(data) {
        return `type-${data.folder.toLowerCase()}`
    }


</script>

<div class="container" class:hide-folder-on-hover={isDeletable}>
    <span class="file-container">
        <span class="icon">
            {#if isDeletable}
                <span class="folder-icon"><FolderSymbol/></span>
                <span class="delete-icon" on:click={() => dispatch("delete", data)}><TrashSymbol/></span>
            {:else}
                <span class="folder-icon"><FolderSymbol/></span>
            {/if}
        </span>
        <span class="file-name" class:enlarged-file-name={sideCardHidden}>{data.folder}</span>
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
            <select name="type" id={getId(data)} bind:value={data.sequenceType} class="type-select" disabled={disabled}>
                <option value="-">-</option>
                <option value="T1">T1</option>
                <option value="T1-KM">T1-KM</option>
                <option value="T2">T2</option>
                <option value="T2*">T2*</option>
                <option value="Flair">Flair</option>
            </select>
        {/if}
    </span>
    
    <span class="file-size-container">
        <span class="file-size">{formatBytes(getSizeOfFiles(data), 1)}</span>
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
        gap: 5px;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
	}
	.container:hover {
		background: #0001;
	}
    .type-select {
        /* all:unset; */
        @media only screen and (min-width: 1700px) {
            width: 50%;
        }
        @media only screen and (max-width: 1699px) {
            width: 75%;
        }
        text-align: center;
        max-width: 100px;
    }
    .icon {
        width: 17px;
        margin: 5px 15px 0px 15px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    /* The file-name class is for  */
    .file-name {
        @media only screen and (min-width: 1700px) {
            width: 350px;
        }
        @media only screen and (min-width: 1350px) and (max-width: 1699px) {
            width: 300px;
        }
        @media only screen and (max-width: 1349px) {
            width: 275px;
        }
		text-overflow: ellipsis;
        white-space: nowrap;
		overflow: hidden;
        align-self: center;
        margin-left: 20px;
        font-size: 15px;
    }
    .file-name.enlarged-file-name {
        @media only screen and (min-width: 1700px) {
            width: 600px;
        }
        @media only screen and (min-width: 1350px) and (max-width: 1699px) {
            width: 550px;
        }
        @media only screen and (max-width: 1349px) {
            width: 500px;
        }
    }
    .preview-button {
        margin: auto;
    }

    .file-container {
        @media only screen and (min-width: 1700px) {
            flex: 1 16 400px;
        }
        @media only screen and (min-width: 1400px) and (max-width: 1699px) {
            flex: 1 12 350px;
        }
        display: flex;
    }
    .preview-container {
        flex: 4;
        display: flex;
    }
    .type-container {
        @media only screen and (min-width: 1750px) {
            flex: 4;
        }
        @media only screen and (min-width: 1500px) and (max-width: 1749px) {
            flex: 5;
        }
        @media only screen and (min-width: 1200px) and (max-width: 1499px) {
            flex: 6;
        }
        display: flex;
        justify-content: center;
    }
	.file-size-container {
		flex: 4;
		text-align: center;
		opacity: .6;
		font-style: italic;
        white-space: nowrap;
        font-size: 14px;
	}
    .file-size {
        user-select: none;
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
        accent-color: var(--button-color-confirm);

    }
	.folder-icon {
		display: block;
	}
	.delete-icon {
		display: none;
	}
	.hide-folder-on-hover:hover .folder-icon {
		display: none;
	}
	.hide-folder-on-hover:hover .delete-icon {
		display: block;
		cursor: pointer;
	}
</style>