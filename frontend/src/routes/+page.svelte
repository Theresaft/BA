<script>
  import PageWrapper from "../single-components/PageWrapper.svelte";
  import Card from "../shared-components/general/Card.svelte";
  import FolderUploader from "../shared-components/folder-uploader/FolderUploader.svelte";
  import OverviewContent from "../shared-components/summary/OverviewContent.svelte";
  import Viewer from "../shared-components/viewer/Viewer.svelte";
  import RecentSegmentationsList from "../shared-components/recent-segmentations/RecentSegmentationsList.svelte"
  import HideSymbol from "../shared-components/svg/HideSymbol.svelte";
  import ShowSymbol from "../shared-components/svg/ShowSymbol.svelte";
  import SubpageStatus from "../shared-components/general/SubpageStatus.svelte"
  import { RecentSegmentations, Projects, isLoggedIn } from "../stores/Store";
  import { onMount } from 'svelte';
  import { uploadProjectDataAPI, startSegmentationAPI, getAllProjectsAPI } from '../lib/api.js';
  import ProjectOverview from "../shared-components/project-overview/ProjectOverview.svelte";
  import SegmentationSelector from "../shared-components/segmentation-selector/SegmentationSelector.svelte";
  import JSZip from 'jszip'
  import Login from "../single-components/Login.svelte";
  import Register from "../single-components/Register.svelte";
  import Modal from "../shared-components/general/Modal.svelte";



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

    // This is the working project for the FolderUploader
    let newProject
    // This is the working project for the SegmentationSelector, which works with an already existing project
    let selectedProject
    // This is a temporary object, which will be added to the currently relevant project (newProject or selectedProject) only after the segmentation
    // is actually started.
    let newSegmentation
    // This name refers to either newProject or of selectedProject.
    let relevantProject

    // Viewer
    let params


    // Check if the user already has is seesion token set
    onMount(() => {
        $isLoggedIn = sessionStorage.getItem('session_token') !== null;
    })

    /**
     * Update the logged in status of the user and load the user's project from the database.
     */
    function handleLoginSuccess() {
        // Change loggin in flag
        $isLoggedIn = true

        // Load project data
        getAllProjectsAPI()
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
            file_format: "dicom", //TODO: get the correct file format
            file_infos: []
        }

        // Get relevant file meta information
        for (let el of project.foldersToFilesMapping) {
            projectInformation.file_infos.push({
                sequence_name: el.folder,
                sequence_type: el.sequence
            })
        }

        formData.append('project_information', JSON.stringify(projectInformation))

        const zip = new JSZip();

        // Zip all dicom files
        for (let el of project.foldersToFilesMapping) {
            let folder = zip.folder(el.folder)
            for (let file of el.files) {
                folder.file(file.name, file)
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
        // In the store, the new project is appended at the end of the existing projects if the variable newProject already exists.
        // This is the case if the user creates a new project. If a segmentation was added to an existing project, we don't add
        // another project to the store.
        if (newProject) {
            $Projects = [...$Projects, newProject]
            // Upload Project and get the sequence IDs and the project ID, as they are stored in the database. This info is then
            // used to start the segmentation below.
            const data = await uploadProject(newProject)

            // Write the sequence IDs into the Projects variable
            for (let el of newProject.foldersToFilesMapping) {
                for (let sequence of data.sequence_ids) {
                    if (sequence.name === el.folder) {
                        el.sequenceID = sequence.id
                    } 
                }
            }

            newProject.projectID = data.project_id

            console.log("Uploaded data:")
            console.log(data)
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
        
        const segmentationObjectToSend = relevantProject.segmentations[relevantProject.segmentations.length - 1]

        let projectID = relevantProject.projectID
        let t1ID = segmentationObjectToSend.sequenceMappings.t1.sequenceID
        let t1kmID = segmentationObjectToSend.sequenceMappings.t1km.sequenceID
        let t2ID = segmentationObjectToSend.sequenceMappings.t2.sequenceID
        let flairID = segmentationObjectToSend.sequenceMappings.flair.sequenceID

        // The data object to send
        let segmentationData = {
            projectID: projectID,
            segmentationName: segmentationObjectToSend.segmentationName,
            t1: t1ID,
            t1km: t1kmID,
            t2: t2ID,
            flair: flairID,
            model: segmentationObjectToSend.model,
        }

        startSegmentationAPI(JSON.stringify(segmentationData));
        
        changeStatus(PageStatus.PROJECT_OVERVIEW)
        
        // The newProject variable is reset again
        newProject = undefined
    }


    /**
     * If the side card is shown, hide it, and vice versa.
     */
    function toggleSideCard() {
        sideCardHidden = !sideCardHidden
    }


    /**
     * Load image to Viewer.
     * @param event The event containing the Nifti ID.
     */
    async function openRecentSegmentationViewer(event) {
        console.log("TODO: Implement");
        //viewerVisible = true
        /* TODO:
            1. Check whether or not segmentation is done
            2. If segmentation is done:
                Get Raw Images and Labels and load into viewer
            3. Else:
                Get Raw Images only and load them into the viewer
        */
        try {
            // Fetch images
            images = await getSegmentationAPI();

            // Load t1 in to the viewer
            params.images = [images.t1];
            window.papaya.Container.resetViewer(0, params); 
            activeBaseImage = "t1"
            imageOrderStack.push("t1")

        } catch (error) {
            console.error('Error loading NIfTI images:', error);
        }
    }


    /**
     * Load local DICOM Images in the Viewer for preview.
     * @param e The event containing the file information.
     */
    function openPreview (e) {
        const files = e.detail.files
        const blobs = []
        for (const file of files) {
            let blob = URL.createObjectURL(file);
            blobs.push(blob)
        }
        params.images = [blobs];
        window.papaya.Container.resetViewer(0, params);
        viewerVisible = true
    }


    /**
     * Close the window by setting the corresponding flag to false.
     */
    function closeViewer() {
        viewerVisible = false
    }
</script>


{#if !$isLoggedIn}
  <!-- Login oder Account-Erstellung anzeigen, abhängig vom Zustand -->
  {#if !isAccountCreation}
      <Login on:loginSuccess={handleLoginSuccess} on:toggleAccountCreation={toggleAccountCreation} />
  {:else}
      <Register on:accountCreated={handleLoginSuccess} on:toggleAccountCreation={toggleAccountCreation} />
  {/if}
{:else}
    <!-- show mainpage else -->
    <PageWrapper>
        <SubpageStatus {statusList} on:statusChanged={subpageStatusChangedByIndex}/>
        <div class="container">
            <!-- The main content depends on the current status of the page. -->
            <div class="card-container" class:blur={viewerVisible}>
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
                            bind:segmentationToAdd={newSegmentation} bind:project={relevantProject} isForExistingProject={!newProject}/>
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
                        <RecentSegmentationsList on:open-viewer={openRecentSegmentationViewer}/>
                    </Card>
                </div>
            {:else}
                <button class="show-symbol-button" on:click={toggleSideCard}>
                    <ShowSymbol/>
                </button>
            {/if}
            </div>

            <!-- Modal Window for Viewer -->
            <div class:hidden={!viewerVisible}>
                <Viewer bind:params={params} previewModeEnabled={true} on:closeViewer={closeViewer}/>
            </div>
        </div>
    </PageWrapper>
  <Modal bind:showModal={showConfirmProjectOverviewModal} on:cancel={cancelProjectOverview} on:confirm={confirmProjectOverview} cancelButtonText="Abbrechen" cancelButtonClass="main-button" 
    confirmButtonText = "Zur Projektübersicht" confirmButtonClass = "confirm-button">
    <h2 slot="header">
        Zurück zur Projektübersicht?
    </h2>
    <p>
        Wollen Sie zurück zur Projektübersicht gehen? Alle nicht gespeicherten Daten werden gelöscht!
    </p>
</Modal>
{/if}


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

</style>