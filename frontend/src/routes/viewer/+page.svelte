<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import Card from "../../shared-components/general/Card.svelte"
    import SearchBar from "../../shared-components/general/SearchBar.svelte"
    import Viewer from "../../shared-components/viewer/Viewer.svelte"
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { Projects, RecentSegmentations } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte"
    import { onMount } from 'svelte'
    import { getSegmentationAPI } from "../../lib/api"


    let showModal = false
    let segmentationToDelete = {}
    let displayedSegmentations = $RecentSegmentations
    let loadedImages;
    let viewerIsLoading = false;
    

    function showDeleteModal(e) {
        showModal = true
        segmentationToDelete = e.detail
    }

    function allSegmentations(){
        const allSegmentations = []
        for (let project of $Projects){

            for (let segmentation of project.segmentations){
                allSegmentations.push(segmentation)
            }
        }
        
        return allSegmentations
    }


    function deleteClicked() {
        // TODO Refactor this (duplicate of ProjectOverview)
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

        // Ensure the components are actually updated on the screen
        reloadProjectEntries = !reloadProjectEntries

        segmentationToDelete = {}
    }


    /**
     * 1) Fetches t1, t1km, t2, flair and all label images from backend
     * 2) saves the URLs of the blobs in "images"
     * 3) Loads t1 sequence in to the viewer 
     */
    async function loadImageToViewer(event) {
        try {
            // Fetch images
            viewerIsLoading = true          
            loadedImages = await getSegmentationAPI(event.detail.segmentationID)            
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
            displayedSegmentations = $RecentSegmentations
        } else {
            displayedSegmentations = $RecentSegmentations.filter(data => {
                return filterFunction(prompt, data)
            })
        }
    }

</script>

<PageWrapper removeMainSideMargin={true} showFooter={false}>
    <div class="container">
        <div class="side-card">
            <Card title="Letzte Segmentierungen" center={true} dropShadow={false} borderRadius={false} width={474}>
                <SearchBar on:promptChanged={filterByPrompt}/>
                {#if allSegmentations().length === 0}
                    <p>Keine Segmentierungen gefunden.</p>
                {:else}
                {#each allSegmentations() as segmentation}
                    <!-- TODO Check if the segmentation is done -->
                    <!-- {#if segmentation.segmentationStatus.id === "done"} -->
                        <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={showDeleteModal} on:view-image={loadImageToViewer}/>
                    <!-- {/if} -->
                {/each}
                {/if}
            </Card>
        </div>

        <Viewer images={loadedImages} bind:viewerIsLoading={viewerIsLoading}/>

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
        position: absolute; /* TODO: remove absolute position and find a better way*/
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        display: flex;
    }
    .side-card {
        display: flex;
        width: 474px;
    }
</style>