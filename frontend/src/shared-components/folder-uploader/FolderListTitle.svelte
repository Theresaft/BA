<script>

</script>

<div class="container">
    <span class="file-container title">
        <h3>Ordnername</h3>
    </span>
    
    <span class="preview-container title">
        <h3>Vorschau ansehen</h3>
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
        flex: 16;
        display: flex;
    }
    .preview-container {
        flex: 4;
    }
    .type-container {
        flex: 4;
    }
	.file-size-container {
		flex: 4;
	}
    .selection-container {
        flex: 2;
    }
    .title {
        display: block;
        font-size: 15px;
        text-align: center;
    }
</style>