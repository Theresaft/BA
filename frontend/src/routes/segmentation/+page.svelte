<script>
    import { fly } from "svelte/transition"
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";
    import OverviewContent from "../../shared-components/OverviewContent.svelte";
    import RecentSegmentationsList from "../../shared-components/RecentSegmentationsList.svelte"
    import HideSymbol from "../../shared-components/svg/HideSymbol.svelte";
    import ShowSymbol from "../../shared-components/svg/ShowSymbol.svelte";
    import { RecentSegmentations, SegmentationStatus, updateSegmentationStatus } from "../../stores/Store";
    import { get } from "svelte/store";

    let uploaderVisible = true
    let overviewVisible = false
    let sideCardHidden = false
    let selectedData = []
    let selectedDataObject = {}
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

    async function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    async function simulateSegmentation() {
        await sleep(3000)
        // Now that the data has been sent successfully and is queuing, reset the data object.
        // selectedDataObject = {}
        updateSegmentationStatus(selectedDataObject.segmentationName, get(SegmentationStatus).QUEUEING)
        await sleep(10000)
        updateSegmentationStatus(selectedDataObject.segmentationName, get(SegmentationStatus).DONE)
    }

    const startSegmentation = (e) => {
        // TODO Send API request with the mapping sequence => files for each sequence to start
        // the segmentation. Do this asynchronously, so the user can do something else in the meantime.
        const segmentationName = e.detail
        selectedDataObject = {
            segmentationName: segmentationName, folderMapping: selectedData,
            scheduleTime: new Date().toISOString(), segmentationStatus: get(SegmentationStatus).PENDING,
            segmentationResult: null 
        }

        $RecentSegmentations = [...$RecentSegmentations, selectedDataObject]
        console.log("Selected data to send to API for segmentation:", selectedData, "with name", segmentationName)
        console.log("Recent segmentations", $RecentSegmentations)

        // TODO Call API here. For now, we add a dummy object that gets segmented after a while.
        // The simulated API call is done in a non-blocking way, so that on the other
        // thread, we can set a timeout that sets the status to "done" after some time.
        console.log("before timeout")
        setTimeout(function() {
            simulateSegmentation()
        }, 0)
        console.log("after timeout")

        overviewVisible = false
        uploaderVisible = true
    }

    const toggleSideCard = () => {
        sideCardHidden = !sideCardHidden
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
        {#if !sideCardHidden}
            <div class="side-card">
                <Card title="Letzte Segmentierungen" center={true} dropShadow={false} on:symbolClick={toggleSideCard}>
                    <div slot="symbol">
                        <HideSymbol/>
                    </div>
                    <RecentSegmentationsList/>
                </Card>
            </div>
        {:else}
            <button class="show-symbol-button" on:click={toggleSideCard}>
                <ShowSymbol/>
            </button>
        {/if}
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
    .show-symbol-button {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: var(--background-color-card);
        border-radius: 7px;
        padding: 10px;
        margin-bottom: auto;
    }
</style>