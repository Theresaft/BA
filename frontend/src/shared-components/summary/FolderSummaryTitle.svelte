<script>

</script>

<div class="container">
    <span class="type-container title">
        <h3>Sequenz</h3>
    </span>

    <span class="file-container title">
        <h3>Ordnername</h3>
    </span>
</div>

<style>
    .container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
        justify-content: center;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
        text-align: left;
        width: 50%;
	}
    .title {
        display: block;
        font-size: 15px;
        text-align: center;
    }
    .type-container {
        flex: 1;
        text-align: left;
        padding-left: 20px;
    }
    .file-container {
        flex: 2;
        text-align: left;
    }
</style>