<script>
  import PageWrapper from "../single-components/PageWrapper.svelte";
  import Card from "../shared-components/general/Card.svelte";
  import FolderUploader from "../shared-components/folder-uploader/FolderUploader.svelte";
  import OverviewContent from "../shared-components/summary/OverviewContent.svelte";
  import Viewer from "../shared-components/viewer/PreviewViewer.svelte";
  import RecentSegmentationsList from "../shared-components/recent-segmentations/RecentSegmentationsList.svelte"
  import HideSymbol from "../shared-components/svg/HideSymbol.svelte";
  import ShowSymbol from "../shared-components/svg/ShowSymbol.svelte";
  import SubpageStatus from "../shared-components/general/SubpageStatus.svelte"
  import { Projects, isLoggedIn, isPolling, startPolling, stopPolling } from "../stores/Store";
  import { onMount } from 'svelte';
  import { uploadProjectDataAPI, startSegmentationAPI, getUserIDAPI, getSingleDicomSequence, getDicomFromNifti } from '../lib/api.js';
  import ProjectOverview from "../shared-components/project-overview/ProjectOverview.svelte";
  import SegmentationSelector from "../shared-components/segmentation-selector/SegmentationSelector.svelte";
  import JSZip from 'jszip'
  import Login from "../single-components/Login.svelte";
  import Register from "../single-components/Register.svelte";
  import Modal from "../shared-components/general/Modal.svelte";
  import { SegmentationStatus } from "../stores/Segmentation";
  import { loadImage } from "../stores/ViewerStore";
  import { goto } from '$app/navigation';
  import { DicomSequence, NiftiSequence } from "../stores/Sequence";
  import { previewImage } from "../stores/ViewerStore"

  // ---- Current state of the segmentation page
  // The hierarchy indicates at what position the corresponding page status should be placed.
    export const PageStatus = {
        PROJECT_OVERVIEW: {name: "Projektübersicht", hierarchy: 0},
        NEW_PROJECT: {name: "Neues Projekt", hierarchy: 1},
        NEW_SEGMENTATION: {name: "Neue Segmentierung", hierarchy: 1},
        SEGMENTATION_CONFIRM: {name: "Bestätigung der Segmentierung", hierarchy: 2},
    }

    // indicates whether the user is in the account creation process (true) or the login process (false).    
    let isAccountCreation = false

    let curPageStatus = PageStatus.PROJECT_OVERVIEW
    let prevPageStatus = undefined
    let statusList = [PageStatus.PROJECT_OVERVIEW]
    // This is the list of subpages that the user has navigated to. The list will be shown in the form of "Element 1" => "Element 2" => ...
    
    let sideCardHidden = false
    let viewerVisible = false
    let showConfirmProjectOverviewModal = false
    // This variable is false if and only if the current page is project overview: Here we don't have any changes to save.
    // Using a reactive value below, this variable is kept in sync with the current PageStatus.
    let pageHasUnsavedChanges = false
    
    // Error variables
    let reloadLoadingSymbol = false
    let showErrorModal = false
    let errorCause = ""

    // Dummy variable to allow reloading of RecentSegmentations list. This explicit reloading happens when a new segmentation is started.
    let reloadRecentSegmentations
    let reloadProjectOverview

    // This is the working project for the FolderUploader
    let newProject
    // This is the working project for the SegmentationSelector, which works with an already existing project
    let selectedProject
    // This is a temporary object, which will be added to the currently relevant project (newProject or selectedProject) only after the segmentation
    // is actually started.
    let newSegmentation
    // This name refers to either newProject or selectedProject.
    let relevantProject

    // Preview Viewer
    let previewSequenceName
    let previewSequenceType
    let showInfoModal = false

    $: {
        pageHasUnsavedChanges = (curPageStatus !== PageStatus.PROJECT_OVERVIEW)
    }


    // Check if the user already has is seesion token set
    onMount(async () => {
        const isValid = await validateToken()
        $isLoggedIn = isValid;
    });


    /**
     * Check if the user_token corresponds to an active session
     */
    async function validateToken() {
        try {
            const userID = await getUserIDAPI();
            return userID !== null;
        } catch (e) {
            console.error("Error validating token:", e);
            return false;
        }
    }


    /**
     * Update the logged in status of the user and load the user's project from the database.
     */
    function handleLoginSuccess() {
        // Change login flag
        $isLoggedIn = true
    }


    /**
     * Toggle between account creation and login
     */
    function toggleAccountCreation() {
        isAccountCreation = !isAccountCreation
    }

    /**
     * Update the current status and the status list
     * @param newStatus The new status to go to
     */
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


    /**
     * Given an index from the status list to go to, change the status at that index.
     * The index is read from the event e.
     * @param e The event from which the index is read.
     */
    function subpageStatusChangedByIndex(e) {
        // Prevent adding a new element when the index is the last one in the list
        // In any other case, go to the intended status.
        const clickedIndex = e.detail
        if (clickedIndex !== statusList.length - 1) {
            // Update previous state status
            prevPageStatus = statusList[statusList.length - 1]
            const newStatus = statusList[e.detail]
            // If we go back to the main page, first ask for confirmation because all entered
            // data will be lost if the user goes back. Otherwise, change the status immediately.
            if (newStatus == PageStatus.PROJECT_OVERVIEW) {
                showConfirmProjectOverviewModal = true
            } else {
                changeStatus(newStatus)
            }
        }
    }


    /**
     * Go back to the second-to-last status, thus removing the last status.
     */
    function goBackInStatus() {
        // If the status list only has at most one element, we will ignore the request
        // to go back a state.
        if (statusList.length > 1) {
            // Update previous state status
            prevPageStatus = statusList[statusList.length - 1]
            const newStatus = statusList[statusList.length - 2]
            // If we go back to the main page, first ask for confirmation because all entered
            // data will be lost if the user goes back. Otherwise, change the status immediately.
            if (newStatus == PageStatus.PROJECT_OVERVIEW) {
                showConfirmProjectOverviewModal = true
            } else {
                changeStatus(newStatus)
            }
        }
    }

    /**
     * If the FolderUploader has caused a classification error, handle it here by showing the error modal.
     */
    function handleClassificationError() {
        showErrorModal = true
        errorCause = "Laden der Sequenzinformationen"
    }


    /**
     * Confirm that the user wants to go back to the project overview.
     */
    function confirmProjectOverview() {
        // Finally, change the status here
        changeStatus(PageStatus.PROJECT_OVERVIEW)
        // Reset the variables for the newProject, the selectedProject and the relevantProject.
        newProject = undefined
        selectedProject = undefined
        relevantProject = undefined
    }


    /**
     * Cancel the project overview transition and don't do the status change.
     */
    function cancelProjectOverview() {
    }


    /**
     * Show the new project screen by changing the status.
     */
    function createProject() {
        changeStatus(PageStatus.NEW_PROJECT)
    }


    /**
     * Show the screen for creating a new segmentation for an existing project.
     * @param e The event containing the selected project.
     */
    function createSegmentation(e) {
        selectedProject = e.detail
        changeStatus(PageStatus.NEW_SEGMENTATION)
    }


    /**
     * When the user closes the folder uploader (the component for creating a new project), the
     * screen for confirming the segmentation info is shown.
     * @param e The event containing the new segmentation to add.
     */
    function closeUploader(e) {
        newSegmentation = e.detail
        relevantProject = newProject
        changeStatus(PageStatus.SEGMENTATION_CONFIRM)
    }


    /**
     * When the user closes the segmentation window (the component for creating a new segmentation),
     * the screen for confirming the segmentation info is shown.
     * @param e The event containing the new segmentation to add.
     */
    function closeSegmentationSelector(e) {
        newSegmentation = e.detail
        relevantProject = selectedProject
        changeStatus(PageStatus.SEGMENTATION_CONFIRM)
    }


    /**
     * Uploads Metadata and Files of the newly created project
     * @param project The project to upload asyncronously.
     */
    async function uploadProject(project) {
        // Create new formData Object
        const formData = new FormData();

        // Get meta Information about the project
        let projectInformation = {
            project_name: project.projectName,
            file_format: project.fileType, //TODO: get the correct file format
            file_infos: []
        }

        // Get relevant file meta information
        switch (project.fileType) {
            case "dicom": {
                for (let el of project.sequences) {
                    projectInformation.file_infos.push({
                        sequence_name: el.folder,
                        sequence_type: el.sequenceType,
                        selected: el.selected,
                        size_in_bytes: el.sizeInBytes
                    })
                }
                break
            }
            case "nifti": {
                for (let el of project.sequences) {
                    projectInformation.file_infos.push({
                        sequence_name: el.fileName,
                        sequence_type: el.sequenceType,
                        selected: el.selected,
                        size_in_bytes: el.sizeInBytes
                    })
                }
                break
            }
        }

        formData.append('project_information', JSON.stringify(projectInformation))

        const zip = new JSZip();

        // Zip all dicom/nifti files
        for (let el of project.sequences) {
            switch (project.fileType) {
                case "dicom": {
                    let folder = zip.folder(el.folder)
                    for (let file of el.files) {
                        folder.file(file.name, file)
                    }
                    break
                }
                case "nifti": {
                    zip.file(el.fileName, el.file)
                    break
                }
            }

        }
        const content = await zip.generateAsync({ type: "blob" });
        
        formData.append('data', content);
        const result = await uploadProjectDataAPI(formData);
        return result;
    }


    /**
     * Start the actual segmentation by sending the segmentation info to the server in the
     * agreed-upon format.
     */
    async function startSegmentation() {
        try {
            // In the store, the new project is appended at the end of the existing projects if the variable newProject already exists.
            // This is the case if the user creates a new project. If a segmentation was added to an existing project, we don't add
            // another project to the store.
            if (newProject) {
                // Upload Project and get the sequence IDs and the project ID, as they are stored in the database. This info is then
                // used to start the segmentation below.
                const data = await uploadProject(newProject)

                // Write the sequence IDs into the Projects variable
                for (let el of newProject.sequences) {
                    for (let sequence of data.sequence_ids) {
                        switch (newProject.fileType) {
                            case "dicom": {
                                if (sequence.name === el.folder) {
                                    el.sequenceID = sequence.id
                                }
                                break
                            } case "nifti": {
                                if (sequence.name === el.fileName) {
                                    el.sequenceID = sequence.id
                                }
                                break
                            }
                        }
                    }
                }
                
                // Assign the fetched project ID from the backend to the new project
                newProject.projectID = data.project_id

                // Finally, add the new project to the list of Projects in the store
                $Projects = [...$Projects, newProject]
            }
            
            let relevantSegmentation = relevantProject.segmentations[relevantProject.segmentations.length - 1]

            let projectID = relevantProject.projectID
            let t1ID = relevantSegmentation.selectedSequences.t1 ?
                relevantSegmentation.selectedSequences.t1.sequenceID : undefined
            let t1kmID = relevantSegmentation.selectedSequences.t1km ?
                relevantSegmentation.selectedSequences.t1km.sequenceID : undefined
            let t2ID = relevantSegmentation.selectedSequences.t2 ?
                relevantSegmentation.selectedSequences.t2.sequenceID : undefined
            let flairID = relevantSegmentation.selectedSequences.flair ?
                relevantSegmentation.selectedSequences.flair.sequenceID : undefined

            // The data object to send
            let segmentationData = {
                projectID: projectID,
                segmentationName: relevantSegmentation.segmentationName,
                t1: t1ID,
                t1km: t1kmID,
                t2: t2ID,
                flair: flairID,
                model: relevantSegmentation.model,
            }

            const response = await startSegmentationAPI(JSON.stringify(segmentationData))
            if (response.ok) {
                // Get the JSON response
                const result = await response.json()
                // Update the segmentation ID for consistent data
                relevantSegmentation.segmentationID = result.segmentation_data.segmentation_id
                relevantSegmentation.dateTime = result.segmentation_data.date_time
                relevantSegmentation.projectName = relevantProject.projectName
                relevantSegmentation.status =  SegmentationStatus[result.segmentation_data.status]

                // If the payload has been sent successfully to the server, delete the corresponding variable
                // contents in the frontend to save memory. The payload is only fetched from the backend on demand.
                // A Project object by itself has no payload, in a Segmentation, data has to be deleted. In a DICOM sequence,
                // files has to be deleted, while in a NIFTI sequence, file is deleted.
                relevantSegmentation.data = null
                if (relevantProject.fileType == "dicom") {
                    for (let seq of relevantProject.sequences) {
                        seq.files = []
                    }
                } else if (relevantProject.fileType == "nifti") {
                    for (let seq of relevantProject.sequences) {
                        seq.file = null
                    }
                } else {
                    // Illegal file type
                    const errorMessage = `Project ${relevantProject.projectName} has illegal file type ${relevantProject.fileType}!`
                    console.error(errorMessage)
                    throw new Error(errorMessage)
                }
            } else {
                // Show error modal indicating that the segmentation failed
                const errorMessage = 'Fehler bei der Anfrage: ' + response.statusText
                console.error(errorMessage)
                throw new Error(errorMessage)
            }

            // (Re-)start polling 
            if($isPolling){
                stopPolling()
            }
            startPolling()

            changeStatus(PageStatus.PROJECT_OVERVIEW)

            // Always update the Projects in the store, since the updating may have been messed up.
            Projects.update(currentProjects => currentProjects.map(project => {
                if (project.projectID === relevantProject.projectID) {
                    return relevantProject
                } else {
                    return project
                }
            }))
            
            // The newProject variable is reset again
            newProject = undefined
        } catch(error) {
            reloadLoadingSymbol = !reloadLoadingSymbol
            showErrorModal = true
            errorCause = "Senden der Projektdaten"
            // The new project or the new segmentation in the frontend object has to be deleted because
            // the creation in the backend wasn't successful.
            // Delete newProject from Store to stay consistent
            if (newProject) {
                // Delete project from store
                $Projects = $Projects.filter(project => project.projectName !== newProject.projectName)
                // Delete created segmentation from project
                newProject.segmentations = []
            // Delete new segmentation from Store to stay consistent
            } else {
                // Delete segmentation that was created last in the existing project
                relevantProject.segmentations.pop()
            }
        }

        console.log("Projects")
        console.log($Projects)

        reloadProjectOverview = !reloadProjectOverview
        // If the segmentation is done (even with an error), reload the recent segmentations list
        updateRecentSegmentations()
    }


    /**
     * A function that toggles the value of reloadRecentSegmentations to reload RecentSegmentationsList
     */
    function updateRecentSegmentations() {
        reloadRecentSegmentations = !reloadRecentSegmentations   
    }


    /**
     * If the side card is shown, hide it, and vice versa.
     */
    function toggleSideCard() {
        sideCardHidden = !sideCardHidden
    }


    /**
     * Load image to Viewer and got to viewer page.
     * @param event The event containing the Segmentation ID.
     */
    async function openSegmentationInViewer(event) {
        try {
            loadImage(event.detail.segmentationID)
            goto('/brainns/viewer');
        } catch (error) {
            console.error('Error loading images:', error);
        }
    }


    /**
     * Load local DICOM Images in the Viewer for preview.
     * @param e The event containing the file information.
     */
    async function openPreview (e) {
        $previewImage = null

        if(e.detail instanceof DicomSequence) {
            previewSequenceName = e.detail.folder
        } else if(e.detail instanceof NiftiSequence) {
            previewSequenceName = e.detail.fileName
        }
        previewSequenceType = e.detail.sequenceType

        viewerVisible = true

        if(curPageStatus === PageStatus.NEW_PROJECT) {
            if(e.detail instanceof DicomSequence) {
                $previewImage = e.detail.files
            } else if(e.detail instanceof NiftiSequence) {
                $previewImage = await nifti2dicom(e.detail.fileName, e.detail.file)
            }
        } else if(curPageStatus === PageStatus.NEW_SEGMENTATION) {
            $previewImage = await getSingleDicomSequence(e.detail.sequenceID)
        }
    }

    async function nifti2dicom(fileName, file) {
		const zip = new JSZip();

		zip.file(fileName, file, {binary: true})

        // Create new formData Object
        const formData = new FormData();
        const content = await zip.generateAsync({type:"blob"})
        // Add Blob to formData Object
        formData.append('nifti_data', content);
        
        // Send nifti file to backend and get the corresponding dicom series
        return await getDicomFromNifti(formData);
    }



    /**
     * Close the window by setting the corresponding flag to false.
     */
    function closePreview() {
        viewerVisible = false
    }

    function closeErrorModal() {
    }
</script>


<!-- show mainpage else -->
<PageWrapper bind:hasUnsavedChanges={pageHasUnsavedChanges}>
    {#if !$isLoggedIn}
    <!-- Login oder Account-Erstellung anzeigen, abhängig vom Zustand -->
        {#if !isAccountCreation}
            <Login on:loginSuccess={handleLoginSuccess} on:toggleAccountCreation={toggleAccountCreation} />
        {:else}
            <Register on:accountCreated={handleLoginSuccess} on:toggleAccountCreation={toggleAccountCreation} />
        {/if}
    {:else}
        <SubpageStatus {statusList} on:statusChanged={subpageStatusChangedByIndex}/>
        <div class="container">
            <!-- The main content depends on the current status of the page. -->
            <div class="card-container" class:blur={viewerVisible}>
            {#if curPageStatus === PageStatus.PROJECT_OVERVIEW}
                {#key reloadProjectOverview}
                    <div class="main-card">
                        <Card title="Projekte" center={true} dropShadow={false}>
                            <ProjectOverview on:createProject={createProject} on:createSegmentation={createSegmentation} on:deleteProject={updateRecentSegmentations}/>
                        </Card>
                    </div>
                {/key}
            {:else if curPageStatus === PageStatus.NEW_PROJECT}
                <div class="main-card">
                    <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                        <FolderUploader on:openViewer={openPreview} on:closeUploader={closeUploader} on:goBack={goBackInStatus} on:classificationError={handleClassificationError} bind:project={newProject} bind:sideCardHidden={sideCardHidden}/>
                    </Card>
                </div>
            {:else if curPageStatus === PageStatus.NEW_SEGMENTATION}
            <div class="main-card">
                <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                    <p class="description">
                        Wählen Sie die Sequenzen für das ausgewählte Projekt aus.Es muss aber, in Abhängigkeit vom ausgewähltem Modell <strong>mindestens ein Ordner</strong> der notwendigen Sequenz ausgewählt werden, also mindestens einer von T1, T2 oder T2*, T1-KM oder Flair. Ihre zuletzt selbst zugwiesenen Sequenztypen für die Ordner wurden gespeichert.
                    </p>
                    <SegmentationSelector on:openViewer={openPreview} on:closeSegmentationSelector={closeSegmentationSelector} on:goBack={goBackInStatus} bind:project={selectedProject} bind:sideCardHidden={sideCardHidden}/>
                </Card>
            </div>
            {:else if curPageStatus === PageStatus.SEGMENTATION_CONFIRM}
                <div class="main-card">
                    <Card title="Übersicht" center={true} dropShadow={false}>
                        <OverviewContent on:startSegmentation={startSegmentation} on:goBack={goBackInStatus} 
                            bind:segmentationToAdd={newSegmentation} bind:project={relevantProject} isForExistingProject={!newProject} {reloadLoadingSymbol}/>
                    </Card>
                </div>
            {/if}

            <!-- Regardless of the current state of the page, the side card can always be shown or hidden. -->
            {#if !sideCardHidden}
                <div class="side-card">
                    <Card title="Segmentierungen" center={true} dropShadow={false} scrollableContentMaxViewportPercentage={53} on:symbolClick={toggleSideCard}>
                        <div slot="symbol">
                            <HideSymbol/>
                        </div>
                        <div slot="scrollable" class="side-card-content">
                            {#key reloadRecentSegmentations}
                                <RecentSegmentationsList on:open-viewer={openSegmentationInViewer}/>
                            {/key}
                        </div>
                    </Card>
                </div>
            {:else}
                <button class="show-symbol-button" on:click={toggleSideCard}>
                    <ShowSymbol/>
                </button>
            {/if}
            </div>

            <!-- Modal Window for Viewer -->
            {#if viewerVisible}
                <Viewer bind:name={previewSequenceName} bind:type={previewSequenceType} on:closeViewer={closePreview} on:openInfoModal={() => showInfoModal = true}/>
            {/if}

            {#if showInfoModal}
            <div class="modal-overlay">
                <div class="modal-box">
                  <h2 class="modal-title">Werkzeuge</h2>
              
                  <!-- Key mappings -->
                  <div class="modal-content">
                    <div class="key-row"><span class="key">Linksklick</span><span>Aktuelles Primär-Tool verwenden</span></div>
                    <div class="key-row"><span class="key">Rechtsklick</span><span>Zoom aktivieren</span></div>
                    <div class="key-row"><span class="key">Mausrad</span><span>Durch Slices navigieren</span></div>
                    <div class="key-row"><span class="key">Mausradklick</span><span>Bild verschieben</span></div>
                    <div class="key-row"><span class="key">Shift + Linksklick</span><span>Window Leveling anpassen</span></div>
                    <div class="key-row"><span class="key">Leertaste</span><span>Zwischen Ansichten wechseln</span></div>
                  </div>
              
                  <div class="modal-footer">
                    <button class="modal-close-btn" on:click={() => showInfoModal = false}>Schließen</button>
                  </div>
                </div>
              </div>
              
            {/if}
        </div>
    {/if}
</PageWrapper>

<!-- The modal is shown as a warning when cancelling the project creation process. -->
<Modal bind:showModal={showConfirmProjectOverviewModal} on:cancel={cancelProjectOverview} on:confirm={confirmProjectOverview} cancelButtonText="Abbrechen" cancelButtonClass="main-button" 
    confirmButtonText = "Zur Projektübersicht" confirmButtonClass = "confirm-button">
    <h2 slot="header">
        Zurück zur Projektübersicht?
    </h2>
    <p>
        Wollen Sie zurück zur Projektübersicht gehen? Alle nicht gespeicherten Daten werden gelöscht!
    </p>
</Modal>

<!-- The modal is shown when some error has occurred. -->
<Modal bind:showModal={showErrorModal} on:cancel={closeErrorModal} cancelButtonText="OK" cancelButtonClass="main-button">
    <h2 slot="header">
        Fehler
    </h2>
    <p>
        {#if errorCause !== ""}
            Ein Fehler beim {errorCause} ist aufgetreten. Bitte versuchen Sie es später noch einmal.
        {:else}
            Ein unbekannter Fehler ist aufgetreten. Bitte versuchen Sie es später noch einmal.
        {/if}
    </p>
</Modal>



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

    .blur {
        filter: blur(10px);
    }
    .hidden {
        display: none;
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

</style>