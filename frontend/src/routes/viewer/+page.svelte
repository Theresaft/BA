<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import Card from "../../shared-components/general/Card.svelte"
    import SearchBar from "../../shared-components/general/SearchBar.svelte"
    import Viewer from "../../shared-components/viewer/Viewer.svelte"
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { Projects } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte"
    import { getRawSegmentationDataAPI, getBaseImagesBySegmentationIdAPI, deleteSegmentationAPI, getSequencesMetadataAPI } from "../../lib/api"
    import {images, viewerIsLoading, viewerState, segmentationLoaded, labelState} from "../../stores/ViewerStore" 
    import {removeSegmentation} from "../../shared-components/viewer/segmentation"
    import { SegmentationStatus } from "../../stores/Segmentation"


    let showDeletionErrorModal = false
    let showLoadingSymbol = false
    let showInfoModal = false;

    let reloadSegmentationEntries

    let displayedSegmentations = [];

    $: {
        let segmentations = $Projects.flatMap(project => project.segmentations).slice()

        // Sort the segmentations in-place so that the latest segmentation is the first in the list, regardless of the project.
        segmentations.sort((segA, segB) => segA.segmentationID < segB.segmentationID)

        // Filter out the segmentations that have an error
        segmentations = segmentations.filter(seg => seg.status != SegmentationStatus["ERROR"])

        displayedSegmentations = segmentations
    }


    async function deleteSegmentation(e) {
        try {
            showLoadingSymbol = true

            const {segmentationID: segmentationID} = e.detail
            const response = await deleteSegmentationAPI(segmentationID)

            if (response.ok) {
                // Update the projects such that only the segmentation from the project in question is deleted.
                Projects.update(currentProjects => currentProjects.map(project => {
                    // This only affects the segmentation in the correct project since the segmentation IDs are valid globally.
                    project.segmentations = project.segmentations.filter(segmentation => segmentation.segmentationID !== segmentationID)
                    return project
                }))
                
                // In case of success, reload the segmentation entries. This updates this variable in ProjectEntry.
                reloadSegmentationEntries = !reloadSegmentationEntries
            } else {
                throw new Error(response.statusText)
            }
        } catch(error) {
            console.error('Error during deletion of segmentation:', error)
            // Delay the display of the modal slightly to not overwhelm the user with modals.
            setTimeout(() => {
                reloadSegmentationEntries = !reloadSegmentationEntries
                showDeletionErrorModal = true
            }, 350)
        }
    }


    /**
     * 1) Fetches t1, t1km, t2, flair and raw segmentation array
     * 2) saves the URLs of the blobs and metadata in "images"
     * -> T1 will be loaded automatically when it is set 
     */
    async function loadImage(event) {
        try {
            // Clear old segmentations if any
            if($viewerState.segmentationId){
                removeSegmentation($viewerState.segmentationId)
                $viewerState.segmentationId = ""

                // Reset labels
                labelState.update(labels =>
                    labels.map(label => ({
                        ...label,
                        opacity: 50,
                        isVisible: true
                    }))
                );

                $segmentationLoaded = false
            }

            // Fetch images and segemntation data
            $viewerIsLoading = true          
            const baseImages = await getBaseImagesBySegmentationIdAPI(event.detail.segmentationID)
            const segmentationData = await getRawSegmentationDataAPI(event.detail.segmentationID)
            const baseImageMetaData = await getSequencesMetadataAPI(event.detail.segmentationID)            

            $images.t1 = baseImages.t1
            $images.t1km = baseImages.t1km
            $images.t2 = baseImages.t2
            $images.flair = baseImages.flair
            $images.labels = segmentationData.segmentation
            $images.maxPixelValueT1 = baseImageMetaData["max-display-value"].t1
            $images.maxPixelValueT1km = baseImageMetaData["max-display-value"].t1km
            $images.maxPixelValueT2 = baseImageMetaData["max-display-value"].t2
            $images.maxPixelValueFlair  = baseImageMetaData["max-display-value"].flair

        } catch (error) {
            console.error('Error:', error);
        }
    }


    /**
     * This is a changable filter function for the typed prompt. The current function compares if the two
     * strings are equal, but one could implement other comparisons like comparing the ID or comparing
     * if the strings are approximately equal.
     **/
    function filterFunction(enteredPrompt, data) {
        return data.segmentationName.toLowerCase().includes(enteredPrompt.toLowerCase()) ||
                data.projectName.toLowerCase().includes(enteredPrompt.toLowerCase())
    }


    function filterByPrompt(e) {
        const prompt = e.detail
        if (prompt === "") {
            displayedSegmentations = $Projects.flatMap(project => project.segmentations)
        } else {
            displayedSegmentations = $Projects.flatMap(project => project.segmentations).filter(data => {
                return filterFunction(prompt, data)
            })
        }
    }

</script>

<PageWrapper removeMainSideMargin={true} showFooter={false}>
    <div class="container" class:blur={showInfoModal}>
        <div class="side-card">
            <Card title="Segmentierungen" center={true} dropShadow={false} borderRadius={false} scrollableContentMaxViewportPercentage={65} width={374}>
                <SearchBar on:promptChanged={filterByPrompt}/>
                <div slot="scrollable">
                    {#if $Projects.flatMap(project => project.segmentations).length === 0}
                        <p>Keine Segmentierungen gefunden.</p>
                    {:else}
                        {#each displayedSegmentations as segmentation}
                            {#key reloadSegmentationEntries}
                                <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={deleteSegmentation} on:view-image={loadImage}/>
                            {/key}
                        {/each}
                    {/if}
                </div>
            </Card>
        </div>
        
        <Viewer on:openInfoModal={() => showInfoModal = true}/>
    </div>
    {#if showInfoModal}
        <div class="modal-overlay">
            <div class="info-modal">
                <h2>Viewer Info</h2>
                <p>Hier ist deine Info oder Erklärung...</p>
                <button on:click={() => showInfoModal = false}>Schließen</button>
            </div>
        </div>
    {/if}

    <!-- Show a modal when the deletion fails. -->
    <Modal bind:showModal={showDeletionErrorModal} on:cancel={() => {reloadSegmentationEntries = !reloadSegmentationEntries}} on:confirm={() => {reloadSegmentationEntries = !reloadSegmentationEntries}} confirmButtonText="OK" confirmButtonClass="main-button">
        <h2 slot="header">
            Löschen fehlgeschlagen
        </h2>
        <p>
            Beim Löschen ist ein Fehler aufgetreten.
        </p>
    </Modal>
</PageWrapper>

<style>
    /*https://stackoverflow.com/questions/5445491/height-equal-to-dynamic-width-css-fluid-layout*/
    .container {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        display: flex;
    }
    .side-card {
        display: flex;
        width: 374px;
    }
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000; 
    }

    .info-modal {
        background-color: var(--background-color-card);
        padding: 2px;
        border-radius: 5px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        max-width: 500px;
        width: 100%;
        text-align: center;
    }

    .info-modal button {
        margin-top: 1.5rem;
        padding: 0.6rem 1.2rem;
        border: none;
        border-radius: 0.5rem;
        background-color: #0070f3;
        color: white;
        font-weight: bold;
        cursor: pointer;
    }

    .info-modal button:hover {
        background-color: #005bb5;
    }
    .blur{
        filter: blur(5px);
    }
</style>