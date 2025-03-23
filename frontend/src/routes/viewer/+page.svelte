<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import Card from "../../shared-components/general/Card.svelte"
    import SearchBar from "../../shared-components/general/SearchBar.svelte"
    import Viewer from "../../shared-components/viewer/Viewer.svelte"
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { Projects } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte"
    import { getRawSegmentationDataAPI, getBaseImagesBySegmentationIdAPI } from "../../lib/api"
    import {images, viewerIsLoading, viewerState} from "../../stores/ViewerStore" 
    import {removeSegmentation} from "../../shared-components/viewer/segmentation"


    let showModal = false
    let segmentationToDelete = {}

    let displayedSegmentations = [];
    $: displayedSegmentations = $Projects.flatMap(project => project.segmentations);

    $: {
        let segmentations = $Projects.flatMap(project => project.segmentations).slice()

        // Sort the segmentations in-place so that the latest segmentation is the first in the list, regardless of the project.
        segmentations.sort((segA, segB) => segA.segmentationID < segB.segmentationID)

        displayedSegmentations = segmentations
    }
    

    function showDeleteModal(e) {
        showModal = true
        segmentationToDelete = e.detail
    }


    function deleteClicked() {
        const projectNameTarget = segmentationToDelete.projectName
        const segmentationNameToDelete = segmentationToDelete.segmentationName

        // Update the projects such that only the segmentation from the project in question is deleted.
        Projects.update(currentProjects => currentProjects.map(project => {
                if (project.projectName === projectNameTarget) {
                    project.segmentations = project.segmentations.filter(segmentation => segmentation.segmentationName !== segmentationNameToDelete)
                }
                
                return project
            })
        )

        segmentationToDelete = {}
    }


    /**
     * 1) Fetches t1, t1km, t2, flair and raw segmentation array
     * 2) saves the URLs of the blobs in "images"
     * 3) Loads t1 sequence in to the viewer 
     */
    async function loadImageToViewer(event) {
        try {
            // Clear old segmentations if any
            if($viewerState.segmentationId){
                removeSegmentation($viewerState.segmentationId)
                $viewerState.segmentationId = ""
            }

            // Fetch images and segemntation data
            $viewerIsLoading = true          
            const baseImages = await getBaseImagesBySegmentationIdAPI(event.detail.segmentationID)
            const segmentationData = await getRawSegmentationDataAPI(event.detail.segmentationID)

            $images.t1 = baseImages.t1
            $images.t1km = baseImages.t1km
            $images.t2 = baseImages.t2
            $images.flair = baseImages.flair
            $images.labels = segmentationData.segmentation

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
    <div class="container">
        <div class="side-card">
            <Card title="Segmentierungen" center={true} dropShadow={false} borderRadius={false} scrollableContent={true} width={374}>
                <SearchBar on:promptChanged={filterByPrompt}/>
                {#if $Projects.flatMap(project => project.segmentations).length === 0}
                    <p>Keine Segmentierungen gefunden.</p>
                {:else}
                {#each displayedSegmentations as segmentation}
                    <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={showDeleteModal} on:view-image={loadImageToViewer}/>
                {/each}
                {/if}
            </Card>
        </div>

        <Viewer />

    </div>
    <Modal bind:showModal on:cancel={() => {}} on:confirm={() => deleteClicked()} cancelButtonText="Abbrechen" cancelButtonClass="main-button" 
        confirmButtonText = "Löschen" confirmButtonClass = "error-button">
        <h2 slot="header">
            Segmentierung löschen?
        </h2>
        <p>
            Soll die Segmentierung <i>{segmentationToDelete.segmentationName}</i> gelöscht werden? Dies kann nicht rückgängig gemacht werden!
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
</style>