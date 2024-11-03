<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/general/Card.svelte";
    import FolderUploader from "../../shared-components/folder-uploader/FolderUploader.svelte";
    import OverviewContent from "../../shared-components/summary/OverviewContent.svelte";
    import RecentSegmentationsList from "../../shared-components/recent-segmentations/RecentSegmentationsList.svelte"
    import HideSymbol from "../../shared-components/svg/HideSymbol.svelte";
    import ShowSymbol from "../../shared-components/svg/ShowSymbol.svelte";
    import SubpageStatus from "../../shared-components/general/SubpageStatus.svelte"
    import { RecentSegmentations, SegmentationStatus, updateSegmentationStatus, Projects } from "../../stores/Store";
    import { get } from "svelte/store";
    import { onDestroy } from 'svelte';
    import CrossSymbol from "../../shared-components/svg/CrossSymbol.svelte"
    import { apiStore } from '../../stores/apiStore';
    import ProjectOverview from "../../shared-components/project-overview/ProjectOverview.svelte";
    import SegmentationSelector from "../../shared-components/segmentation-selector/SegmentationSelector.svelte";

    // ---- Current state of the segmentation page
    // The hierarchy indicates at what position the corresponding page status should be placed.
    export const PageStatus = {
        PROJECT_OVERVIEW: {name: "Projektübersicht", hierarchy: 0},
        NEW_PROJECT: {name: "Neues Projekt", hierarchy: 1},
        NEW_SEGMENTATION: {name: "Neue Segmentierung", hierarchy: 1},
        SEGMENTATION_CONFIRM: {name: "Bestätigung der Segmentierung", hierarchy: 2},
    }

    let curPageStatus = PageStatus.PROJECT_OVERVIEW
    let statusList = [PageStatus.PROJECT_OVERVIEW]
    // This is the list of subpages that the user has navigated to. The list will be shown in the form of "Element 1" => "Element 2" => ...
    
    let sideCardHidden = false
    let selectedData = []
    let allData = []
    let windowVisible = false

    // This is the working project for the FolderUploader
	let newProject
    // This is the working project for the SegmentationSelector, which works with an already existing project
    let selectedProject
    // This is a temporary object, which will be added to the currently relevant project (newProject or selectedProject) only after the segmentation
    // is actually started.
    let newSegmentation
    // This name refers to either newProject or of selectedProject.
    let relevantProject

    // papaya viewer config
    let params = { 
      kioskMode: true,
      showSurfacePlanes: true, 
      showControls: false
    }

    // Update the current status and the status list
    function changeStatus(newStatus) {
        
        const previousStatus = statusList[statusList.length - 1]
        
        if (previousStatus.hierarchy > newStatus.hierarchy) {
            // Find the first index whose hierarchy is the same as the new hierarchy value, replace the value at that index with the new
            // status and remove all elements after that.
            const sliceIndex = statusList.findIndex(status => status.hierarchy === newStatus.hierarchy)
            statusList = statusList.slice(0, sliceIndex)
        }

        // In any case, we append the new status at the end of the list.
        curPageStatus = newStatus
        statusList = [...statusList, newStatus]
    }

    function subpageStatusChangedByIndex(e) {
        // Prevent adding a new element when the index is the last one in the list
        // In any other case, go to the intended status.
        const clickedIndex = e.detail
        if (clickedIndex !== statusList.length - 1) {
            const newStatus = statusList[e.detail]
            changeStatus(newStatus)
        }
    }

    function goBackInStatus() {
        // If the status list only has at most one element, we will ignore the request
        // to go back a state.
        if (statusList.length > 1) {
            const newStatus = statusList[statusList.length - 2]
            changeStatus(newStatus)
        }
    }

    const createProject = () => {
        changeStatus(PageStatus.NEW_PROJECT)
    }

    const createSegmentation = (e) => {
        selectedProject = e.detail
        changeStatus(PageStatus.NEW_SEGMENTATION)
    }

    const closeUploader = (e) => {
        newSegmentation = e.detail
        relevantProject = newProject
        changeStatus(PageStatus.SEGMENTATION_CONFIRM)
    }

    const closeSegmentationSelector = (e) => {
        newSegmentation = e.detail
        relevantProject = selectedProject
        changeStatus(PageStatus.SEGMENTATION_CONFIRM)
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
        changeStatus(PageStatus.NEW_PROJECT)
    }

    async function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    const startSegmentation = () => {
        // In the store, the new project is appended at the end of the existing projects if the variable newProject already exists.
        // This is the case if the user creates a new project. If a segmentation was added to an existing project, we don't add
        // another project to the store.
        if (newProject) {
            $Projects = [...$Projects, newProject]
        }

        // For debugging
        console.log("Projects:")
        console.log($Projects)

        // Collect the data from the relevant project, i.e., either the new project or the
        // selected project. It is sufficient for a unique representation of the recent segmentations
        // to only store the project name and the segmentation name: Due to uniqueness, it is ensured
        // that given these two variables, you can find the correct segmentation. When the other relevant
        // info on the segmentation is to be loaded (e.g., the time the segmentation was started), this
        // information can be retrieved from the store's $Project variable.
        const mostRecentSegmentation = {
            projectName: relevantProject.projectName,
            segmentationName: relevantProject.segmentations[relevantProject.segmentations.length - 1].segmentationName
        }
        
        // Add the most recent segmentation to the list of segmentations
        $RecentSegmentations = [...$RecentSegmentations, mostRecentSegmentation]
        
        // TODO Send API request with the mapping sequence => files for each sequence to start
        // the segmentation. Do this asynchronously, so the user can do something else in the meantime.
        

        /*
        let projectID = $apiStore.projectCreationResponse.project_id

        let segmentationData = {
            segmentation_name: segmentationName,
            project_id: projectID,
            t1: selectedData.find(obj => obj.sequence === "T1").sequenceId,
            t1km: selectedData.find(obj => obj.sequence === "T1-KM").sequenceId,
            t2: selectedData.find(obj => obj.sequence === "T2" || obj.sequence === "T2*").sequenceId,
            flair: selectedData.find(obj => obj.sequence === "Flair").sequenceId,
            selected_model: selectedModel
        }

        // Trigger the store to upload the files
		apiStore.startSegmentation(JSON.stringify(segmentationData));
        */
        changeStatus(PageStatus.PROJECT_OVERVIEW)
        // The newProject variable is reset again
        newProject = undefined
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
        let imageUUID = imageUrl.split('/').pop();
        params[imageUUID] = {lut: "Spectrum"};
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

    const changeColorMap = (colorMap) => {
        papayaContainers[0].viewer.screenVolumes[0].changeColorTable(papayaContainers[0].viewer, colorMap)
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
    <SubpageStatus {statusList} on:statusChanged={subpageStatusChangedByIndex}/>
    <div class="container">
        <!-- The main content depends on the current status of the page. -->
        <div class="card-container" class:blur={windowVisible}>
        {#if curPageStatus === PageStatus.PROJECT_OVERVIEW}
            <div class="main-card">
                <Card title="Projekte" center={true} dropShadow={false}>
                    <ProjectOverview on:createProject={createProject} on:createSegmentation={createSegmentation}/>
                </Card>
            </div>
        {:else if curPageStatus === PageStatus.NEW_PROJECT}
            <div class="main-card">
                <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                    <FolderUploader on:openViewer={openPreview} on:closeUploader={closeUploader} on:goBack={goBackInStatus} bind:project={newProject} bind:sideCardHidden={sideCardHidden}/>
                </Card>
            </div>
        {:else if curPageStatus === PageStatus.NEW_SEGMENTATION}
        <div class="main-card">
            <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                <p class="description">
                    Wählen Sie die Sequenzen für das ausgewählte Projekt aus. Es muss von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden, also jeweils mindestens einer von T1, T2 oder T2*, T1-KM und Flair. Ihre zuletzt selbst zugwiesenen Sequenztypen für die Ordner wurden gespeichert.
                </p>
                <SegmentationSelector on:openViewer={openPreview} on:closeSegmentationSelector={closeSegmentationSelector} on:goBack={goBackInStatus} bind:project={selectedProject} bind:sideCardHidden={sideCardHidden}/>
            </Card>
        </div>
        {:else if curPageStatus === PageStatus.SEGMENTATION_CONFIRM}
            <div class="main-card">
                <Card title="Übersicht" center={true} dropShadow={false}>
                    <OverviewContent on:startSegmentation={startSegmentation} on:goBack={goBackInStatus} 
                        bind:segmentationToAdd={newSegmentation} bind:project={relevantProject} disableProjectName={!newProject}/>
                </Card>
            </div>
        {/if}

        <!-- Regardless of the current state of the page, the side card can always be shown or hidden. -->
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
                        <button on:click={() => {changeColorMap("Grayscale")}}>A</button>
                        <button on:click={() => {changeColorMap("Spectrum")}}>B</button>
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