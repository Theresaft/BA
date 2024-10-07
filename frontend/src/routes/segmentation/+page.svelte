<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/general/Card.svelte";
    import FolderUploader from "../../shared-components/folder-uploader/FolderUploader.svelte";
    import OverviewContent from "../../shared-components/summary/OverviewContent.svelte";
    import RecentSegmentationsList from "../../shared-components/recent-segmentations/RecentSegmentationsList.svelte"
    import HideSymbol from "../../shared-components/svg/HideSymbol.svelte";
    import ShowSymbol from "../../shared-components/svg/ShowSymbol.svelte";
    import { RecentSegmentations, SegmentationStatus, updateSegmentationStatus } from "../../stores/Store";
    import { get } from "svelte/store";
    import { onDestroy } from 'svelte';
    import CrossSymbol from "../../shared-components/svg/CrossSymbol.svelte"
    import { apiStore } from '../../stores/apiStore';

    let uploaderVisible = true
    let overviewVisible = false
    let sideCardHidden = false
    let selectedData = []
    let selectedDataObject = {}
    let allData = []
    let windowVisible = false

    // papaya viewer config
    let params = { 
      kioskMode: true ,
      showSurfacePlanes: true, 
      showControls: false
    }

    const closeUploader = (e) => {
        let data = e.detail
        uploaderVisible = false

        selectedData = getSelectedData(data)
        overviewVisible = true
    }

    const getSelectedData = (data) => {
        // This is a simple dummy implementation of the actual selection algorithm.
        // For each sequence, select the first folder in the list. Due to previous input
        // validation, it is guaranteed that all sequences occur.
        let sequences = ["T1-KM", "T1", "T2", "Flair"]
        let selectedData = []

		for (let seq of sequences) {
            const def = data.find(obj => obj.sequence === seq || seq === "T2" && obj.sequence === "T2*")
            const best = data.reduce((min,item) => {
                const correctSequenceType = item.sequence === seq || seq === "T2" && item.sequence === "T2*"
                if(correctSequenceType && item.resolution < min.resolution) {
                    return item
                } else return min
            }, def)
			selectedData.push(best)
		}

        return selectedData
    }
    
    // Go back from the overview page to the uploader page, while maintaining all the previously entered data by the user.
    const goBack = () => {
        overviewVisible = false
        uploaderVisible = true
    }

    async function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    async function simulateSegmentation() {
        await sleep(3000)
        // Now that the data has been sent successfully and is queueing, reset the data object.
        // selectedDataObject = {}
        updateSegmentationStatus(selectedDataObject.segmentationName, get(SegmentationStatus).QUEUEING)
        await sleep(10000)
        updateSegmentationStatus(selectedDataObject.segmentationName, get(SegmentationStatus).DONE)
    }

    const startSegmentation = (e) => {
        // TODO Send API request with the mapping sequence => files for each sequence to start
        // the segmentation. Do this asynchronously, so the user can do something else in the meantime.
        const segmentationName = e.detail[0]
        const selectedModel = e.detail[1]
        selectedDataObject = {
            segmentationName: segmentationName, folderMapping: selectedData,
            scheduleTime: new Date().toISOString(), segmentationStatus: get(SegmentationStatus).PENDING,
            segmentationResult: null 
        }

        $RecentSegmentations = [...$RecentSegmentations, selectedDataObject]

        let projectID = $apiStore.projectCreationResponse.project_id

        let segmentationData = {
            segmentation_name: segmentationName,
            project_id: projectID,
            t1: selectedData.find(obj => obj.sequence === "T1").sequenceId,
            t1km: selectedData.find(obj => obj.sequence === "T1-KM").sequenceId,
            t2: selectedData.find(obj => obj.sequence === "T2" || "T2*").sequenceId,
            flair: selectedData.find(obj => obj.sequence === "Flair").sequenceId,
            selected_model: selectedModel
        }

        // Trigger the store to upload the files
		apiStore.startSegmentation(JSON.stringify(segmentationData));

        // The simulated API call is done in a non-blocking way, so that on the other
        // thread, we can set a timeout that sets the status to "done" after some time.
        setTimeout(function() {
            simulateSegmentation()
        }, 0)

        overviewVisible = false
        uploaderVisible = true
    }

    const toggleSideCard = () => {
        sideCardHidden = !sideCardHidden
    }

    // Load image to Viewer
    const openViewer = async(event) => {
        // Trigger the store to fetch the blob
        await apiStore.getNiftiById(event.detail.id);

        // Wait until the store's `blob` is updated
        let imageBlob;
        $: imageBlob = $apiStore.blob;

        let imageUrl = URL.createObjectURL(imageBlob);
        params.images = [imageUrl];
        window.papaya.Container.resetViewer(0, params);

        windowVisible = true
    }

    // Load local DICOM Images in the Viewer for preview
    const openPreview = (e) => {
        const files = e.detail.files
        const blobs = []
        for (const file of files) {
            let blob = URL.createObjectURL(file);
            blobs.push(blob)
        }
        params.images = [blobs];
        window.papaya.Container.resetViewer(0, params);
        windowVisible = true
    }
    
    const closeViewer = () => {
        windowVisible = false
    }

    // Removing all Papaya Containers. This is important since papaya will create a new container/viewer each time the page is loaded
    onDestroy(() => {
        if (typeof window !== 'undefined' && window.papaya) {
            window.papayaContainers = []
        } 
    });


</script>


<PageWrapper>
    <div class="container">
        <!-- Main content with cards and side section -->
        <div class="card-container" class:blur={windowVisible}>
        {#if uploaderVisible}
            <div class="main-card">
                <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                    <p class="description">
                        Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern. Es muss aber von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden.
                    </p>
                    <FolderUploader on:openViewer={openPreview} on:closeUploader={closeUploader} bind:foldersToFilesMapping={allData}/>
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
                    <RecentSegmentationsList on:open-viewer={openViewer}/>
                </Card>
            </div>
        {:else}
            <button class="show-symbol-button" on:click={toggleSideCard}>
                <ShowSymbol/>
            </button>
        {/if}
        </div>

        <!-- Modal Window for Viewer -->
        <div class:hidden={!windowVisible}>
            <div class="modal-container">
                <div class="modal-window">
                    <!-- Toolbar for Viewer -->
                    <div class="viewer-toolbar">
                        <button on:click={() => console.log("a")}>A</button>
                        <button on:click={() => console.log("b")}>B</button>
                        <span><strong>Name:</strong> {String("MPR_3D_T1_TFE_tra_neu_602")}</span>
                        <span><strong>Assigned Type:</strong> {String("T1")}</span>
                        <button id="close-button" on:click={closeViewer}> 
                            <CrossSymbol/>
                        </button>       

                    </div>
                    <!-- Papaya  Viewer-->
                    <div class="viewer">
                        <div class="papaya"></div>
                    </div>
                </div>
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
    .show-symbol-button {
        all: unset;
        cursor: pointer;
        display: block;
        background-color: var(--background-color-card);
        border-radius: 7px;
        padding: 10px;
        margin-bottom: auto;
    }
    /* Modal Window for the viewer */
    /* TODO: Handle Ultra Wide Screens*/
    .modal-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000; 
    }

    .modal-window{
        display: flex;
        flex-direction: column;
        width: 55%; 
        margin-top: 4%;
    }
    .viewer{
        width: 100%;
        padding: 0px;
        background-color: rgb(255, 255, 255);
        border-top: 8px solid #ffffff; 
        border-bottom: 8px solid #ffffff;
        border-bottom-left-radius: 5px; 
        border-bottom-right-radius: 5px;
    }
    .viewer-toolbar {
        margin: 0px;
        padding: 0px 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        background-color: #000000;
        border-top-left-radius: 5px; 
        border-top-right-radius: 5px;
    }

    .viewer-toolbar button {
        flex: 0 0 auto;
        background-color: #007bff;
        color: white;
        border: none;
        padding: 8px 16px;
        margin: 5px 5px;
        cursor: pointer;
        border-radius: 7px;
    }
    #close-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 35px;
        height: 35px; 
        border-radius: 50%; 
        background-color: #6c6c6c; /* TODO: CHANGE COLOR */
        padding: 0;
    }

    .viewer-toolbar span {
        flex: 1; 
        font-size: 20px;
        text-align: center;
        padding: 8px 16px;
        margin: 5px 5px; 
    }

    .blur {
        filter: blur(10px);
    }
    .hidden {
        display: none;
    }

</style>