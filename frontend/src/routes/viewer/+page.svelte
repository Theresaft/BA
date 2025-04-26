<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import Card from "../../shared-components/general/Card.svelte"
    import SearchBar from "../../shared-components/general/SearchBar.svelte"
    import Viewer from "../../shared-components/viewer/Viewer.svelte"
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { Projects, UserSettings } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte"
    import { getRawSegmentationDataAPI, getBaseImagesBySegmentationIdAPI, deleteSegmentationAPI, getSequencesMetadataAPI } from "../../lib/api"
    import {images, viewerIsLoading, viewerState, segmentationLoaded, labelState, resetWindowLeveling} from "../../stores/ViewerStore" 
    import {removeSegmentation} from "../../shared-components/viewer/segmentation"
    import { SegmentationStatus } from "../../stores/Segmentation"
    import { loadImage } from "../../stores/ViewerStore"


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
                                <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={deleteSegmentation} on:view-image={(event) => loadImage(event.detail.segmentationID)}/>
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
        <div class="modal-box">
          <h2 class="modal-title">🧠 Werkzeuge</h2>
      
          <!-- Key mappings -->
          <div class="modal-content">
            <div class="key-row"><span class="key">Linksklick</span><span>Aktuelles Primär-Tool verwenden</span></div>
            <div class="key-row"><span class="key">Rechtsklick</span><span>Zoom aktivieren</span></div>
            <div class="key-row"><span class="key">Mausrad</span><span>Durch Slices navigieren</span></div>
            <div class="key-row"><span class="key">Shift + Linksklick</span><span>Window Leveling anpassen</span></div>
            <div class="key-row"><span class="key">Leertaste</span><span>Zwischen Ansichten wechseln</span></div>
          </div>
      
          <!-- Explanation about tools -->
          <div class="tool-info">
            <h3 class="tool-title">🛠 Primär-Tools</h3>
            <p>
              In der rechten oberen Ecke können Sie ein Primär-Tool auswählen. Zur Verfügung stehen:
            </p>
            <ul>
              <li> Pfadenkreuz zum Navigieren</li>
              <li> Messwerkzeug </li>
              <li> Radierer zum Entfernen von Messungen</li>
              <li> Window Leveling (Helligkeit/Kontrast)</li>
            </ul>
            <p>Nur ein Primär-Tool kann gleichzeitig aktiv sein und kann mit der linken Maustaste verwendet werden.</p>
          </div>
      
          <div class="modal-footer">
            <button class="modal-close-btn" on:click={() => showInfoModal = false}>Schließen</button>
          </div>
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


    /* INFO MODAL */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-box {
        background-color: #1a2b44;
        color: white;
        border-radius: 16px;
        width: 500px;
        padding: 24px;
        box-shadow: 0 0 20px rgba(0,0,0,0.3);
    }

    .modal-title {
        font-size: 1.5rem;
        font-weight: bold;
        border-bottom: 1px solid white;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }

    .modal-content {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .key-row {
        display: flex;
        justify-content: space-between;
        font-size: 1rem;
    }

    .key {
        font-weight: bold;
        color: #7dcfff;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
    }

    .tool-info {
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid #ffffff33;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #e0e0e0;
    }

    .tool-title {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }

    .modal-footer {
        display: flex;
        justify-content: flex-end;
        margin-top: 20px;
    }

    .modal-close-btn {
        background: white;
        color: #1a2b44;
        font-weight: bold;
        padding: 6px 16px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.3s ease;
    }

    .modal-close-btn:hover {
     background: #d3d3d3;
    }

    .blur{
        filter: blur(5px);
    }
</style>