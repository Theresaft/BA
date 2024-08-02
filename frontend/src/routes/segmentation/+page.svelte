<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";
    import OverviewContent from "../../shared-components/OverviewContent.svelte";
    import RecentSegmentationsList from "../../shared-components/RecentSegmentationsList.svelte"

    let uploaderVisible = true
    let overviewVisible = false
    let selectedData = []
    let allData = []

    const closeUploader = (e) => {
        let data = e.detail
        uploaderVisible = false
        console.log("Sent data", data)
        
        // TODO Send API request to get the DICOM sequences with the best resolution.
        selectedData = getSelectedData(data)
        
        console.log("Selected data", data)
        overviewVisible = true
        console.log("All data:", allData)
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
    
    // Go back from the overview page to the uploader page, while maintaining all the previously entered data by the user.
    const goBack = () => {
        overviewVisible = false
        uploaderVisible = true
        console.log("All data:", allData)
    }

    const startSegmentation = (e) => {
        // TODO Send API request with the mapping sequence => files for each sequence to start
        // the segmentation. Do this asynchronously, so the user can do something else in the meantime.
        const segmentationName = e.detail
        console.log("Selected data to send to API for segmentation:", selectedData, "with name", segmentationName)

        // TODO Call API here

        overviewVisible = false
        uploaderVisible = true
    }
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        <div class="card-container">
        {#if uploaderVisible}
            <div class="main-card">
                <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                    <p class="description">
                        Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern. Es muss aber von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden.
                    </p>
                    <FolderUploader on:closeUploader={closeUploader} bind:foldersToFilesMapping={allData}/>
                </Card>
            </div>
        {:else if overviewVisible}
            <div class="main-card">
                <Card title="Übersicht" center={true} dropShadow={false}>
                    <OverviewContent on:goBack={goBack} on:startSegmentation={startSegmentation} {selectedData}/>
                </Card>
            </div>
        {/if}
        <div class="side-card">
            <Card title="Letzte Segmentierungen" center={true} dropShadow={false}>
                <RecentSegmentationsList/>
            </Card>
        </div>
        </div>
    </div>
</PageWrapper>


<style>
    .description {
        margin: 20px 0;
    }
    .card-container {
        display: flex;
        flex-direction: row;
        gap: 20px;
    }
    .main-card {
        flex: 2;
    }
    .side-card {
        flex: 1;
    }
</style>