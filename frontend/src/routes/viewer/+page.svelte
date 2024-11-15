<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import Card from "../../shared-components/general/Card.svelte"
    import SearchBar from "../../shared-components/general/SearchBar.svelte"
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { Projects, RecentSegmentations } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte"
    import { onDestroy, onMount } from 'svelte'
    import { getSegmentationAPI, getNiftiByIdAPI } from '../../lib/api'
    import JSZip from 'jszip'
    import dicomParser from 'dicom-parser'

    let showModal = false
    let segmentationToDelete = {}
    let displayedSegmentations = $RecentSegmentations

    // Papaya viewer config
    let params = { 
      kioskMode: true ,
      showSurfacePlanes: true, 
      showControls: false,
      showImageButtons: true,
      // Custom Colormaps for papaya viewer
      luts: [
            {
                "name": "AllRed",
                "data": [
                    [0, 1, 0, 0],
                    [1, 1, 0, 0]   
                ]
            },
            {
                "name": "AllBlue",
                "data": [
                    [0, 0, 0, 1],
                    [1, 0, 0, 1]  
                ]
            },
            {
                "name": "AllGreen",
                "data": [
                    [0, 0, 1, 0], 
                    [1, 0, 1, 0]   
                ]
            },
            {
                "name": "AllYellow",
                "data": [
                    [0, 1, 1, 0],  
                    [1, 1, 1, 0]   
                ]
            }
        ]
    }

    let showRuler = false

    // Corresponds to the loaded images and is either "DICOM" or "NIFTI"
    let fileType
    $: noSegmentationsToShow = () => {
        return $RecentSegmentations.length === 0
    }

    /**
     * Holds all images URLs for raw images (e.g. t1) and segmentation labels.
     * - t1, t1km, t2, flair hold a single URL String when nifti and an array of URLs when DICOM
     * - Labels are always niftis
     */
    let images = {
        t1: null,
        t1km: null,
        t2: null,
        flair: null,
        labels: []
    }

    // List of all labels that are currently visible
    let activeLabels = [] // represented by: 0, 1 and 2

    // The base images that is currently visible 
    let activeBaseImage = "" // "t1", "tkm", "t2" or "flair"

    /**
     * Keeps track of the order of all the loaded images including the labels: e.g. [t1,t1km,t2,flair,0,1,2]
     * Should have the same order as: papayaContainers[0].viewer.screenVolumes
     */
    let imageOrderStack = []


    onMount(()=>{
        window.papaya.Container.resetViewer(0, params);
    })


    // Removing all Papaya Containers. This is important since papaya will create a new container/viewer each time the page is loaded
    onDestroy(() => {
        if (typeof window !== 'undefined' && window.papaya) {
            window.papayaContainers = []
        } 
    })


    /**
     * 1) Fetches t1, t1km, t2, flair and all label images from backend
     * 2) converts the images to blobs and saves the URLs in "images"
     * 3) Loads t1 sequence in to the viewer 
     */
    async function loadImages () {
        try {
            // Fetch images
            const res = await getSegmentationAPI();
            const imageData = res[0]
            fileType = res[1]

            // Intialize "images" based on file type
            images.t1 = fileType === "NIFTI" ? null : [];
            images.t1km = fileType === "NIFTI" ? null : [];
            images.t2 = fileType === "NIFTI" ? null : [];
            images.flair = fileType === "NIFTI" ? null : [];


            // Save image URLs in "images"
            const zip = await JSZip.loadAsync(imageData);
            const promises = [];

            zip.forEach((relativePath, file) => {
                const sequenceType = relativePath.split('/')[0];

                const promise = file.async('blob').then(imageFile => {
                    const url = URL.createObjectURL(imageFile);
                    
                    if (['t1', 't1km', 't2', 'flair'].includes(sequenceType)) {
                        if (fileType === "NIFTI") {
                            images[sequenceType] = url;
                        } else {
                            images[sequenceType].push(url);
                        }
                    } else {
                        images.labels = [...images.labels, url]
                    }
                });

                promises.push(promise);
            });

            await Promise.all(promises);

            // Load t1 in to the viewer
            params.images = [images.t1];
            window.papaya.Container.resetViewer(0, params); 
            activeBaseImage = "t1"
            imageOrderStack.push("t1")

        } catch (error) {
            console.error('Error loading NIfTI images:', error);
        }
    };


    /**
     * Hides the current base image and shows a new base image.
     * Loads the base image to the viewer if it hasn't been loaded already
     * @param baseImage The new base image (t1,t1km,t2 or flair)
     */
    async function showBaseImage(baseImage) {

        // Check if image exists
        if (!images[baseImage]) {
            console.error(`Image "${baseImage}" not found.`);
            return;  
        }

        // Hide old base image
        const index = imageOrderStack.indexOf(activeBaseImage);
        papaya.Container.hideImage(0, index);

        // If the selected base image is already loaded, show it otherwise load it
        if(imageOrderStack.includes(baseImage)){
            // If the selected base image is already loaded, show it
            const imageIndex = imageOrderStack.indexOf(baseImage);
            papaya.Container.showImage(0, imageIndex)
            // Update papaya's currentScreenVolume, so that we update the correct image when changing the contrast
            papayaContainers[0].viewer.currentScreenVolume = papayaContainers[0].viewer.screenVolumes[imageIndex]
        } else{
            loadBaseImage(baseImage)
        }

        activeBaseImage = baseImage
    }


    /**
     * Loads a base image to the viewer
     * If a label is already loaded, the base image is moved behind the label,
     * so that labels are always displayed above the base image
     * @param baseImage
     */
    async function loadBaseImage(baseImage) {

        // Array from papaya that holds image data of a viewer
        let screenVolumes = papayaContainers[0].viewer.screenVolumes
        // Number of loaded images before the update
        let screenVolumeLengthBeforeUpdate = screenVolumes.length

        // Load the base image to the viewer using a grayscale colormap
        let options = {}
        if(fileType === "NIFTI"){
            let imageUrl = images[baseImage];
            let imageUUID = imageUrl.split('/').pop();
            options = {
                [imageUUID]: { lut: "Grayscale" } // Note: imageUUID is the file name used by papaya for niftis
            }
            papaya.Container.addImage(0, imageUrl, options);
        } else {
            let imageUrls = images[baseImage]
            let seriesDescription = await getDICOMDescription(imageUrls[0])
            options = {
                [seriesDescription]: { lut: "Grayscale" } // Note: Papaya uses the dicom series description as file name for dicom series
            }
            papaya.Container.addImage(0, imageUrls, options);
        }

        // Move the base image behind any label image if any labels are already loaded
        let index_first_label = imageOrderStack.findIndex(label => label === 0 || label === 1 || label === 2)

        if (index_first_label === -1) {
            imageOrderStack.push(baseImage);
        } else {
            // Periodically checking if the loading of base image is complete before moving the image behind the label 
            const intervalId = setInterval(function() {

                if (screenVolumeLengthBeforeUpdate + 1 === screenVolumes.length ) {
                    // update image order stack
                    imageOrderStack.splice(index_first_label, 0, baseImage);
                    let lastElement = screenVolumes.pop();
                    // update images in papaya viewer
                    screenVolumes.splice(index_first_label, 0, lastElement);
                    papayaContainers[0].viewer.drawViewer(true, false)

                    clearInterval(intervalId);
                }

            }, 50);
        }
    }


    /**
     * Toggle the visibilty of a label. Load if necessary
     * @param label_index (e.g. 0,1,2)
     */
    function toggleLabel(label_index) {

        if (!imageOrderStack.includes(label_index)) {
            // Load label if it hasn't been loaded yet
            loadLabel(label_index)
        } else {
            // If the label is already loaded: Toggle the visibility
            const index = imageOrderStack.indexOf(label_index);

            if (!activeLabels.includes(label_index)) {
                papaya.Container.showImage(0, index);
                activeLabels = [...activeLabels, label_index]
            } else {
                papaya.Container.hideImage(0, index);
                activeLabels = activeLabels.filter(index => index !== label_index);
            }
        }
    };


    /**
     * Load a label image to the viewer
     * @param label_index (e.g. 0,1,2)
     */
    function loadLabel(label_index) {
        let labelImageUrl = images.labels[label_index]
        let imageUUID = labelImageUrl.split('/').pop();

        // Set color of the label
        let lutColor = "";
        if (label_index === 0) {
            lutColor = "AllRed";
        } else if (label_index === 1) {
            lutColor = "AllYellow";
        } else if (label_index === 2) {
            lutColor = "AllGreen";
        }

        let options = {
            [imageUUID]: { lut: lutColor } //Note: imageUUID is the file name used by papaya for nifties
        };

        // Load label to the viewer
        papaya.Container.addImage(0, labelImageUrl, options);
        activeLabels = [...activeLabels, label_index]
        imageOrderStack.push(label_index);

        // Since we loaded a label image, papaya sets "currentScreenVolume" to this label
        // We need to change the "currentScreenVolume" back to the visible base image
        // This is necessary for example for changing the contrast of the current base image
        let screenVolumes = papayaContainers[0].viewer.screenVolumes
        let screenVolumeLengthBeforeUpdate = screenVolumes.length
        const intervalId = setInterval(function() {
            if (screenVolumeLengthBeforeUpdate + 1 === screenVolumes.length ) {
                const imageIndex = imageOrderStack.indexOf(activeBaseImage);
                papayaContainers[0].viewer.currentScreenVolume = screenVolumes[imageIndex]
                clearInterval(intervalId);
            }
        }, 50);
    }


    // Toggle visibilty of the ruler
    function toggleRuler() {
        papayaContainers[0].preferences.showRuler = showRuler ? "No" : "Yes";
        papayaContainers[0].viewer.drawViewer();
        showRuler = !showRuler;
    }


    // Change the colormap of the visible base image
    function changeColorMap(colorMap) {
        let activeBaseImage_index = imageOrderStack.indexOf(activeBaseImage);        
        papayaContainers[0].viewer.screenVolumes[activeBaseImage_index].changeColorTable(papayaContainers[0].viewer, colorMap)
    }


    // Open the key references
    function openReferenceDialog(title, referenceData) {
        let dialog = new papaya.ui.Dialog(
                    papayaContainers[0],
                    title,
                    referenceData,
                    papaya.Container,
                    null, null, null, true
                );
        dialog.showDialog();
    }


    // Returns the DICOM series Description of a single DICOM file given the image url of the file
    async function getDICOMDescription(imageUrl) {
        // Convert url to blob
        const response = await fetch(imageUrl);
        const blob = await response.blob();

        const arrayBuffer = await blob.arrayBuffer();
        const byteArray = new Uint8Array(arrayBuffer);

        const dataSet = dicomParser.parseDicom(byteArray);

        // Extract Series Description
        const seriesDescription = dataSet.string('x0008103e'); // Series Description tag
        return seriesDescription
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
        const niftiBlob = await getNiftiByIdAPI(event.detail.id);

        let imageUrl = URL.createObjectURL(niftiBlob);
        params.images = [imageUrl];
        window.papaya.Container.resetViewer(0, params);
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
        <div class="viewer-container">
            <div class="viewer"> 
                <!-- Papaya  Viewer-->
                <div class="papaya-viewer">
                    <div class="papaya"></div>
                </div>
                <!-- Toolbar for Viewer -->
                <div class="viewer-toolbar">
                    <button on:click={toggleRuler}>Ruler</button>
                    <button on:click={() => changeColorMap("Grayscale")}>Gray</button>
                    <button on:click={() => changeColorMap("Spectrum")}>Spectrum</button>
                    <span><strong>Name:</strong> {String("MPR_3D_T1_TFE_tra_neu_602")}</span>
                    <!--<span><strong>Assigned Type:</strong> {String("T1")}</span>-->
                    <button on:click={() => openReferenceDialog("Keyboard Reference", papaya.ui.Toolbar.KEYBOARD_REF_DATA)}>Key-Ref</button>
                    <button on:click={() => openReferenceDialog("Mouse Reference", papaya.ui.Toolbar.MOUSE_REF_DATA)}>Mouse-Ref</button>
                </div>
            </div>
            <div class="viewer-sidebar">
                <button on:click={loadImages}>Load</button>

                <button 
                    class={activeBaseImage === "t1" ? "active" : ""} 
                    on:click={() => showBaseImage("t1")}
                >T1</button>
                
                <button 
                    class={activeBaseImage === "t1km" ? "active" : ""} 
                    on:click={() => showBaseImage("t1km")}
                >T1km</button>
                
                <button 
                    class={activeBaseImage === "t2" ? "active" : ""} 
                    on:click={() => showBaseImage("t2")}
                >T2</button>
                
                <button 
                    class={activeBaseImage === "flair" ? "active" : ""} 
                    on:click={() => showBaseImage("flair")}
                >Flair</button>

                {#each images.labels as label, index}
                    <button 
                        class={activeLabels.includes(index) ? "active" : ""} 
                        on:click={() => toggleLabel(index)}
                    >Label {index + 1}
                    </button>               
                 {/each}
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
        width: 474px;
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
            width: 75%;
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
    .viewer-sidebar {
        margin: 0px;
        padding: 0px 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 10px;
        background-color: #000000;
    }

    .viewer-toolbar button,
    .viewer-sidebar button {
        flex: 0 0 auto;
        background-color: #007bff;
        color: white;
        border: none;
        padding: 8px 16px;
        margin: 5px 5px;
        cursor: pointer;
        border-radius: 7px;
    }
    .viewer-sidebar button.active {
        background-color: #dd00ff; /* Active button color */
        color: white;             /* Text color for active button */
        border: none; /* Optional: active border color */
    }

    .viewer-toolbar span {
        flex: 1; 
        font-size: 20px;
        text-align: center;
        padding: 8px 16px;
        margin: 5px 5px; 
    }
</style>