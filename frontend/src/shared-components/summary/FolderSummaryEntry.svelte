<script>
    export let data = {}
</script>

<div class="container">
    <span class="type-container">
        <span class="type">{data.sequence}</span>
    </span>

    <span class="file-container">
        <span class="file-name">{data.folder}</span>
    </span>
</div>

<style>
    .container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
        flex-direction: row;
		align-items: center;
        justify-content: center;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
        width: 50%;
        padding: 10px 0;
	}
	.container:hover {
		background: #0001;
	}
    .file-name {
        white-space: nowrap;
		overflow: hidden;
		/* width: 15ch; */
		text-overflow: ellipsis;
        align-self: center;
		/* display: block; */
		/* font-weight: 300; */
    }

    .file-container {
        flex: 2;
        display: flex;
        text-align: left;
    }
    .type-container {
        flex: 1;
        display: flex;
        text-align: left;
        padding-left: 20px;
    }
</style>