<script>
    export let sequenceMappings = []

	// TODO Make this globally available
	let variablesToStringMapping = {
		t1: "T1",
		t2: "T2/T2*",
		t1km: "T1-KM",
		flair: "Flair"
	}

</script>

<div class="summary">
    <div class="title-container">
		<span class="type-container title">
			<h3>Sequenz</h3>
		</span>
	
		<span class="file-container title">
			<h3>Ordnername</h3>
		</span>
	</div>
	{#each Object.entries(sequenceMappings) as [sequence, data]}
		<div class="entry-container">
			<span class="type-container">
				<span class="type">{variablesToStringMapping[sequence]}</span>
			</span>
		
			<span class="file-container">
				<span class="file-name" title={data.folder}>{data.folder}</span>
			</span>
		</div>
	{/each}
</div>

<style>
	.summary {
		display: flex;
		justify-content: center;
		align-items: center;
		flex-direction: column;
		transition: background-color .3s ease;
		padding-left: 0;
		display: flex;
		flex-direction: column;
		padding: 0;
        margin-bottom: 50px;
	}
	.title-container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
        justify-content: center;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
        text-align: left;
        width: 70%;
	}
	.entry-container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
		align-items: center;
        justify-content: center;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
        text-align: left;
        width: 70%;
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
	.entry-container {
		transition: background-color .2s ease-in-out;
		list-style: none;
		display: flex;
        flex-direction: row;
		align-items: center;
        justify-content: center;
		/* border-radius: 3px; */
        border-bottom: 1px solid var(--font-color-main);
        width: 70%;
        padding: 10px 0;
	}
	.entry-container:hover {
		background: #0001;
	}
    .file-name {
        align-self: center;
		text-overflow: ellipsis;
        white-space: nowrap;
		overflow: hidden;
		@media only screen and (min-width: 17000x) {
			max-width: 450px;
		}
		@media only screen and (min-width: 1400px) and (max-width: 1699px) {
			max-width: 400px;
        }
		@media only screen and (max-width: 1399px) {
			max-width: 350px;
        }
    }

    .file-container {
        flex: 3;
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