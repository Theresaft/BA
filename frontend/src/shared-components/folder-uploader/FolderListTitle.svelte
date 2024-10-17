<script>
    export let sideCardHidden = false
</script>

<div class="container">
    <span class="file-container title">
        <h3 class="file-name" class:enlarged-file-name={sideCardHidden}>Ordnername</h3>
    </span>
    
    <span class="preview-container title">
        <h3>Vorschau</h3>
    </span>
    
    <span class="type-container title">
        <h3>Sequenz</h3>
    </span>
    
    <span class="file-size-container title" class:shrunk-selection={!sideCardHidden}>
        <h3>Größe</h3>
    </span>
    
    <span class="selection-container title" class:shrunk-selection={!sideCardHidden}>
        <h3>A</h3>
    </span>
</div>

<style>
    span {
        user-select: none;
    }
    .container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
        justify-content: center;
		padding: 0px 8px;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
        text-align: center;
	}
    .file-container {
        @media only screen and (min-width: 1700px) {
            flex: 1 16 400px;
        }
        @media only screen and (max-width: 1699px) {
            flex: 1 12 350px;
        }
        display: flex;
    }
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
        margin-left: 67px;
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

    .file-container {
        @media only screen and (min-width: 1700px) {
            flex: 1 16 400px;
        }
        @media only screen and (min-width: 1350px) and (max-width: 1699px) {
            flex: 1 12 350px;
        }
        @media only screen and (max-width: 1349px) {
            flex: 1 10 325px;
        }
        display: flex;
    }

    .preview-container {
        flex: 4;
    }
    .type-container {
        @media only screen and (min-width: 1750px) {
            flex: 4;
        }
        @media only screen and (min-width: 1500px) and (max-width: 1749px) {
            flex: 5;
        }
        @media only screen and (max-width: 1499px) {
            flex: 6;
        }
    }
	.file-size-container {
        flex: 4;
        @media only screen and (min-width: 1500px) and (max-width: 1749px) {
            margin-right: 0;
            text-align: center;
        }
	}
    .selection-container {
        flex: 1;
        visibility: hidden !important;
    }
    .title {
        display: block;
        font-size: 15px;
        text-align: center;
    }
</style>