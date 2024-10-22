<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/general/Card.svelte";
    import SearchBar from "../../shared-components/general/SearchBar.svelte";
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { RecentSegmentations, deleteSegmentation } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte";
    import { onDestroy, onMount } from 'svelte';
    import { apiStore } from '../../stores/apiStore';
    import JSZip from 'jszip';


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
      showControls: false,
      showImageButtons: true,
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

    // All base images and labels 
    let images = {
        t1: null,
        t1km: null,
        t2: null,
        flair: null,
        labels: []
    };

    // All Labels that are currently visible
    let activeLabels = []
    let activeBaseImage = ""

    // Keeps track of all the loaded images including the labels: e.g. [t1,t1km,t2,flair,0,1,2]
    // Should have the same order as: papayaContainers[0].viewer.screenVolumes 
    let loadedImages = []

    const loadImages = async () => {
        try {
            // Fetch the zip file from the backend
            const response = await fetch(`http://localhost:5001/brainns-api/projects/1/segmentations/1`, {
                method: 'GET',
            });

            if (!response.ok) {
                throw new Error(`Error fetching NIfTI images: ${response.statusText}`);
            }

            // Get the zip file as a Blob
            const zipBlob = await response.blob();

            // Initialize JSZip to extract the contents of the zip file
            const zip = await JSZip.loadAsync(zipBlob);

            const promises = [];

            // Loop through each file in the zip
            zip.forEach((relativePath, zipEntry) => {
                // Only process .nii and .nii.gz files
                if (zipEntry.name.endsWith('.nii') || zipEntry.name.endsWith('.nii.gz')) {
                    // Create a promise for processing this entry
                    const promise = zipEntry.async('blob').then(niftiFile => {
                        // Determine the type of the NIfTI file based on its suffix
                        if (zipEntry.name.endsWith('0000.nii') || zipEntry.name.endsWith('0000.nii.gz')) {
                            images.t1 = niftiFile;
                        } else if (zipEntry.name.endsWith('0001.nii') || zipEntry.name.endsWith('0001.nii.gz')) {
                            images.t1km = niftiFile;
                        } else if (zipEntry.name.endsWith('0002.nii') || zipEntry.name.endsWith('0002.nii.gz')) {
                            images.t2 = niftiFile;
                        } else if (zipEntry.name.endsWith('0003.nii') || zipEntry.name.endsWith('0003.nii.gz')) {
                            images.flair = niftiFile;
                        } else {
                            // Everything else goes into the labels array
                            images.labels.push(niftiFile);
                        }
                    });

                    // Push the promise into the array
                    promises.push(promise);
                }
            });
            
            await Promise.all(promises);

            console.log('Images loaded:', images);
            let t1ImageUrl = URL.createObjectURL(images["t1"]);


            params.images = [t1ImageUrl];
            window.papaya.Container.resetViewer(0, params);   

            
            activeBaseImage = "t1"
            loadedImages.push("t1")

        } catch (error) {
            console.error('Error loading NIfTI images:', error);
        }
    };

    const toggleRuler = () => {
        papayaContainers[0].preferences.showRuler = showRuler ? "No" : "Yes";
        papayaContainers[0].viewer.drawViewer();
        showRuler = !showRuler;
    }

    const changeColorMap = (colorMap) => {
        let activeBaseImage_index = loadedImages.indexOf(activeBaseImage);        
        papayaContainers[0].viewer.screenVolumes[activeBaseImage_index].changeColorTable(papayaContainers[0].viewer, colorMap)
    }

    const openReferenceDialog = (title, referenceData) => {
        let dialog = new papaya.ui.Dialog(
                    papayaContainers[0],
                    title,
                    referenceData,
                    papaya.Container,
                    null, null, null, true
                );
        dialog.showDialog();
    }

    const loadBaseImage = (baseImage) => {

        // Check if image exists
        if (!images[baseImage]) {
            console.error(`Image "${baseImage}" not found.`);
            return;  
        }

        // Find base image if exists and hide it
        // TODO: Could simply hide the one active image
        const baseImages = ["t1", "t1km", "t2", "flair"];
        baseImages.forEach((img) => {
            if (loadedImages.includes(img)) {
                const index = loadedImages.indexOf(img);
                papaya.Container.hideImage(0, index);
            }
        });

        // If the selected base image is already loaded, show it otherwise load it
        if(loadedImages.includes(baseImage)){
            const imageIndex = loadedImages.indexOf(baseImage);
            papaya.Container.showImage(0, imageIndex)

            papayaContainers[0].viewer.currentScreenVolume = papayaContainers[0].viewer.screenVolumes[imageIndex]

        }else{
            let screenVolumes = papayaContainers[0].viewer.screenVolumes
            let screenVolumeLengthBeforeAdding = screenVolumes.length

            // Load Image to the Viewer
            let imageUrl = URL.createObjectURL(images[baseImage]);
            let imageUUID = imageUrl.split('/').pop();
            let options = {
                [imageUUID]: { lut: "Gray" }
            };
            
            papaya.Container.addImage(0, imageUrl, options);

            let index_first_label = loadedImages.findIndex(el => el === 0 || el === 1 || el === 2)

            if (index_first_label === -1) {
                loadedImages.push(baseImage);
            } else {
                const intervalId = setInterval(function() {

                    if (screenVolumeLengthBeforeAdding + 1 === screenVolumes.length ) {
                        loadedImages.splice(index_first_label, 0, baseImage);
                        //
                        let lastElement = screenVolumes.pop();
                        screenVolumes.splice(index_first_label, 0, lastElement);
                        papayaContainers[0].viewer.drawViewer(true, false)

                        clearInterval(intervalId);
                    }

                }, 50);
            }
            // Update the active Base Image
        }

        activeBaseImage = baseImage
        console.log(loadedImages);
    }

    const toggleLabel = (label_index) => {

        // Load label if it hasn't been loaded yet
        if (!loadedImages.includes(label_index)) {
            let labelImageUrl = URL.createObjectURL(images.labels[label_index]);
            let imageUUID = labelImageUrl.split('/').pop();

            let lutColor = "";
            if (label_index === 0) {
                lutColor = "AllRed";
            } else if (label_index === 1) {
                lutColor = "AllYellow";
            } else if (label_index === 2) {
                lutColor = "AllGreen";
            }

            let options = {
                [imageUUID]: { lut: lutColor }
            };
            papaya.Container.addImage(0, labelImageUrl, options);
            
            // Label is loaded and active
            //activeLabels.push(label_index); 
            activeLabels = [...activeLabels, label_index]

            loadedImages.push(label_index);

            const imageIndex = loadedImages.indexOf(activeBaseImage);
            console.log("imageIndex:" + imageIndex);
            
            // Wait until Label has been loaded completely and then update the currentScreenVolume back to the active Base Image
            let screenVolumes = papayaContainers[0].viewer.screenVolumes
            let screenVolumeLengthBeforeAdding = screenVolumes.length
            const intervalId = setInterval(function() {
                if (screenVolumeLengthBeforeAdding + 1 === screenVolumes.length ) {
                    papayaContainers[0].viewer.currentScreenVolume = screenVolumes[imageIndex]
                    clearInterval(intervalId);
                }

            }, 50);

        } else {
            const index = loadedImages.indexOf(label_index);

            if (!activeLabels.includes(label_index)) {
                papaya.Container.showImage(0, index);
                activeLabels = [...activeLabels, label_index]
            } else {
                papaya.Container.hideImage(0, index);
                // Remove the label from activeLabels
                activeLabels = activeLabels.filter(index => index !== label_index);
            }
        }
        console.log(loadedImages);
    };

    $: noSegmentationsToShow = () => {
        console.log("bla:", $RecentSegmentations.filter(obj => obj.segmentationStatus.id === "done"))
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
                    on:click={() => loadBaseImage("t1")}
                >T1</button>
                
                <button 
                    class={activeBaseImage === "t1km" ? "active" : ""} 
                    on:click={() => loadBaseImage("t1km")}
                >T1km</button>
                
                <button 
                    class={activeBaseImage === "t2" ? "active" : ""} 
                    on:click={() => loadBaseImage("t2")}
                >T2</button>
                
                <button 
                    class={activeBaseImage === "flair" ? "active" : ""} 
                    on:click={() => loadBaseImage("flair")}
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
    <Modal bind:showModal on:cancel={() => {}} on:confirm={() => deleteClicked()} cancelButtonText = "Abbrechen" cancelButtonClass = "main-button" 
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