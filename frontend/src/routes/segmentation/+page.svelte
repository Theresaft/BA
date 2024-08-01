<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";
    import OverviewContent from "../../shared-components/OverviewContent.svelte";

    let uploaderVisible = true
    let overviewVisible = false
    let selectedData = []

    const closeUploader = (e) => {
        let data = e.detail
        uploaderVisible = false
        console.log("Sent data", data)
        
        // TODO Send API request to get the DICOM sequences with the best resolution.
        selectedData = getSelectedData(data)
        
        console.log("Selected data", data)
        overviewVisible = true
    }

    const getSelectedData = (data) => {
        // This is a simple dummy implementation of the actual selection algorithm.
        // For each sequence, select the first folder in the list. Due to previous input
        // validation, it is guaranteed that all sequences occur.
        let sequences = ["T1-KM", "T1", "T2", "Flair"]
        let selectedData = []

		for (let seq of sequences) {
			selectedData.push(data.find(obj => obj.sequence === seq))
		}

        return selectedData
    }
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        {#if uploaderVisible}
            <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                <p class="description">
                    Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern. Es muss aber von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden.
                </p>
                <FolderUploader on:closeUploader={closeUploader}/>
            </Card>
        {:else if overviewVisible}
            <Card title="Übersicht" center={true} dropShadow={false}>
                <OverviewContent {selectedData}/>
            </Card>
        {/if}
    </div>
</PageWrapper>


<style>
    .description {
        margin: 20px 0;
    }
</style>