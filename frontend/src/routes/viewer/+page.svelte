<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/general/Card.svelte";
    import SearchBar from "../../shared-components/general/SearchBar.svelte";
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { RecentSegmentations, deleteSegmentation } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte";
    import { onDestroy, onMount } from 'svelte';
    import { apiStore } from '../../stores/apiStore';


    let showModal = false
    let segmentationToDelete = {}
    let displayedSegmentations = $RecentSegmentations

    // This is a changable filter function for the typed prompt. The current function compares if the two
    // strings are equal, but one could implement other comparisons like comparing the ID or comparing
    // if the strings are approximately equal.
    const filterFunction = (enteredPrompt, data) => {
        return data.segmentationName.toLowerCase().includes(enteredPrompt.toLowerCase())
    }

    // papaya viewer config
    let params = { 
      kioskMode: true ,
      showSurfacePlanes: true, 
      showControls: false
    }

    $: noSegmentationsToShow = () => {
        return $RecentSegmentations.filter(obj => obj.segmentationStatus.id === "done").length === 0
    }

    const showDeleteModal = (e) => {
        showModal = true
        segmentationToDelete = e.detail
    }

    const deleteClicked = () => {
        deleteSegmentation(segmentationToDelete.segmentationName)
        segmentationToDelete = {}
    }
    // Load image to Viewer
    const loadImageToViewer = async(event) => {
        // Trigger the store to fetch the blob
        await apiStore.getNiftiById(event.detail.id);

        // Wait until the store's `blob` is updated
        let imageBlob;
        $: imageBlob = $apiStore.blob;
         
        let imageUrl = URL.createObjectURL(imageBlob);
        params.images = [imageUrl];
        window.papaya.Container.resetViewer(0, params);
    }

    onMount(()=>{
        window.papaya.Container.resetViewer(0, params);
    });

    // Removing all Papaya Containers. This is important since papaya will create a new container/viewer each time the page is loaded
    onDestroy(() => {
        if (typeof window !== 'undefined' && window.papaya) {
            window.papayaContainers = []
        } 
    });

    function filterByPrompt(e) {
        const prompt = e.detail
        if (prompt === "") {
            displayedSegmentations = $RecentSegmentations
        } else {
            displayedSegmentations = $RecentSegmentations.filter(data => filterFunction(prompt, data))
        }
    }

</script>

<PageWrapper removeMainSideMargin={true} showFooter={false}>
    <div class="container">
        <div class="side-card">
            <Card title="Letzte Segmentierungen" center={true} dropShadow={false} borderRadius={false}>
                <SearchBar on:promptChanged={filterByPrompt}/>
                {#each displayedSegmentations as segmentation}
                    {#if segmentation.segmentationStatus.id === "done"}
                        <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={showDeleteModal} on:view-image={loadImageToViewer}/>
                    {/if}
                {/each}
                {#if noSegmentationsToShow()}
                    <p class="no-segmentations-hint">Keine fertigen Segmentierungen vorhanden.</p>
                {/if}
            </Card>
        </div>
        <div class="viewer-container">
            <div class="viewer"> 
                <!-- Papaya  Viewer-->
                <div class="papaya-viewer">
                    <div class="papaya"></div>
                </div>
                <!-- Toolbar for Viewer -->
                <div class="viewer-toolbar">
                    <button on:click={() => console.log("a")}>A</button>
                    <button on:click={() => console.log("b")}>B</button>
                    <span><strong>Name:</strong> {String("MPR_3D_T1_TFE_tra_neu_602")}</span>
                    <span><strong>Assigned Type:</strong> {String("T1")}</span>
                    <button on:click={() => console.log("b")}>B</button>
                </div>
            </div>
        </div>
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
    }

    /* Modal Window for the viewer */
    .viewer-container{
        flex: 1; /* Take up the rest of the width*/
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: rgb(0, 0, 0);
    }
    .viewer{
        display: flex;
        flex-direction: column;

        /* For an aspect ratio of 1.88, 85% is the perfect width. All aspect ratios wider than that require a smaller
        with because otherwise, the viewer will cover the navbar or even stretch beyond the viewport. */
        width: 85%;

        @media (min-aspect-ratio: 1.8801) and (max-aspect-ratio: 1.92) {
            width: 80%;
        }
        @media (min-aspect-ratio: 1.9201) and (max-aspect-ratio: 2.04) {
            width: 75%;
        }
        @media (min-aspect-ratio: 2.0401) and (max-aspect-ratio: 2.12) {
            width: 70%;
        }
        @media (min-aspect-ratio: 2.1201) and (max-aspect-ratio: 2.22) {
            width: 65%;
        }
        @media (min-aspect-ratio: 2.2201) and (max-aspect-ratio: 2.34) {
            width: 60%;
        }
        @media (min-aspect-ratio: 2.3401) and (max-aspect-ratio: 2.53) {
            width: 55%;
        }
        @media (min-aspect-ratio: 2.5301) and (max-aspect-ratio: 2.75) {
            width: 50%;
        }
        @media (min-aspect-ratio: 2.7501) and (max-aspect-ratio: 3.02) {
            width: 45%;
        }
        @media (min-aspect-ratio: 3.02) and (max-aspect-ratio: 3.32) {
            width: 40%;
        }
        @media (min-aspect-ratio: 3.32) {
            width: 35%;
        }
    }
    .papaya-viewer{
        padding: 0px;
        background-color: #ffffff;
        border-top: 8px solid #ffffff; 
        border-bottom: 8px solid #ffffff;
        border-radius: 5px; 
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

    .viewer-toolbar span {
        flex: 1; 
        font-size: 20px;
        text-align: center;
        padding: 8px 16px;
        margin: 5px 5px; 
    }
</style>