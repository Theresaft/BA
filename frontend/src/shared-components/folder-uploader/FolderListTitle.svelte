<script>
    export let sideCardHidden = false
</script>

<div class="container">
    <span class="file-container title" class:enlarged-file-title={sideCardHidden}>
        <h3>Ordnername</h3>
    </span>
    
    <span class="preview-container title">
        <h3>Vorschau</h3>
    </span>
    
    <span class="type-container title">
        <h3>Sequenz</h3>
    </span>
    
    <span class="file-size-container title">
        <h3>Größe</h3>
    </span>
    
    <span class="selection-container title">
        <h3>Auswahl</h3>
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
        @media only screen and (min-width: 1700px) {
            flex: 1 16 400px;
        }
        @media only screen and (min-width: 1400px) and (max-width: 1699px) {
            flex: 1 12 350px;
        }
        @media only screen and (max-width: 1399px) {
            flex: 1 12 325px;
        }
        display: flex;
    }
    .file-container.enlarged-file-title {
        @media only screen and (min-width: 1700px) {
            flex: 13;
        }
        @media only screen and (min-width: 1350px) and (max-width: 1699px) {
            flex: 16;
        }
        @media only screen and (max-width: 1349px) {
            flex: 18;
        }
        text-align: left;
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
        @media only screen and (min-width: 1500px) {
            flex: 4;
        }
        @media only screen and (max-width: 1499px) {
            flex: 5;
            text-align: left !important;
        }
	}
    .selection-container {
        flex: 2;
        @media only screen and (max-width: 1499px) {
            display: none !important;
        }
    }
    .title {
        display: block;
        font-size: 15px;
        text-align: center;
    }
</style>