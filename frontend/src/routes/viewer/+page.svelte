<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import Card from "../../shared-components/general/Card.svelte"
    import SearchBar from "../../shared-components/general/SearchBar.svelte"
    import Viewer from "../../shared-components/viewer/Viewer.svelte"
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { Projects, RecentSegmentations } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte"
    import { onMount } from 'svelte'


    let showModal = false
    let segmentationToDelete = {}
    let displayedSegmentations = $RecentSegmentations
    
	let params ;

    $: noSegmentationsToShow = () => {
        return $RecentSegmentations.length === 0
    }

    function showDeleteModal(e) {
        showModal = true
        segmentationToDelete = e.detail
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


    // Load image to Viewer
    async function loadImageToViewer(event) {
        // Trigger the store to fetch the blob
        // event.detail.id
        console.log("TODO: Implement");
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

    /**
     * We need to reset the viewer to apply all the viewer settings from the beginning (e.g. kiosk mode)
     * Resetting the viewer inside the viewer component leads to a timing issue because papaya hasn't fully
     * created the viewer when onMount in the viewer component is called.
     * Therefore we bind the params of the viewer to this page component and reset the viewer here
    */
    onMount(()=>{
        window.papaya.Container.resetViewer(0, params);
    })
</script>

<PageWrapper removeMainSideMargin={true} showFooter={false}>
    <div class="container">
        <div class="side-card">
            <Card title="Letzte Segmentierungen" center={true} dropShadow={false} borderRadius={false} width={474}>
                <SearchBar on:promptChanged={filterByPrompt}/>
                {#if noSegmentationsToShow()}
                    <p class="no-segmentations-hint">Keine fertigen Segmentierungen vorhanden.</p>
                {:else if displayedSegmentations.length === 0}
                    <p>Keine Segmentierungen gefunden.</p>
                {:else}
                {#each displayedSegmentations as segmentation}
                    <!-- TODO Check if the segmentation is done -->
                    <!-- {#if segmentation.segmentationStatus.id === "done"} -->
                        <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={showDeleteModal} on:view-image={loadImageToViewer}/>
                    <!-- {/if} -->
                {/each}
                {/if}
            </Card>
        </div>
        <Viewer bind:params={params} /> 
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