import {writable, readable, get} from "svelte/store"

export let viewerState = writable({
    renderingEngine: null,
    renderingEngineId: "MY_RENDERING_ENGINE_ID",
    toolGroup: null,
    toolGroupId: "MY_TOOL_GROUP_ID",
    viewportIds: ["CT_AXIAL", "CT_SAGITTAL", "CT_CORONAL"],
    voiSynchronizerId : "VOI_SYNCHRONIZER_ID",
    volumeId: "",
    segmentationId: "",
    referenceImageIds: [],
    skipOverlapping: false,
    segImageIds: [],
    currentlyDisplayedModality : "", 
    activePrimaryTool : "", // Primary Tools = left click tool
    currentWindowLeveling: {
        t1 : {
            min : 0,
            max : 0
        },
        t1km : {
            min : 0,
            max : 0
        },
        t2 : {
            min : 0,
            max : 0
        },
        flair : {
            min : 0,
            max : 0
        }
    }

})



/**
 * Holds all images Blobs for raw images (e.g. t1) and segmentation labels.
 * - t1, t1km, t2, flair hold a single Blob when nifti and an array of Blobs when DICOM
 * - Labels are always niftis
 */
export let images = writable({
    t1: null,
    t1km: null,
    t2: null,
    flair: null,
    labels: [],
    fileType : "",  // Corresponds to the loaded images and is either "DICOM" or "NIFTI"
    windowLeveling: {
        t1 : {
            minMax: {
                min : 0,
                max : 0
            },
            dicomTag: {
                min : 0,
                max : 0
            }
        },
        t1km : {
            minMax: {
                min : 0,
                max : 0
            },
            dicomTag: {
                min : 0,
                max : 0
            }
        },
        t2 : {
            minMax: {
                min : 0,
                max : 0
            },
            dicomTag: {
                min : 0,
                max : 0
            }
        },
        flair : {
            minMax: {
                min : 0,
                max : 0
            },
            dicomTag: {
                min : 0,
                max : 0
            }
        }
    }

})

 
// Note: Opacity is set to 50 since it is the default for alphaFill (cornerstone), see: segmentation.config.style.getStyle()
export let labelState = writable([
    { name: 'Necrotic Core', opacity: 50, isVisible: true, segmentIndex: 1 },
    { name: 'Enhancing Tumor', opacity: 50, isVisible: true, segmentIndex: 2 },
    { name: 'Edema', opacity: 50, isVisible: true, segmentIndex: 3 }
]); 

export let viewerAlreadySetup = writable(false)

export let viewerIsLoading = writable(false);

export let segmentationLoaded = writable(false)

 // Reads in windowLevling from image state and writes it to viewer state 
// (type must either be "minMax" or "dicomTag")
export function resetWindowLeveling(type){
    viewerState.update(state => {
        const updatedWindowLeveling = {};

        // Loop through modalities
        for (const modality of ["t1", "t1km", "t2", "flair"]) {
            const windowLeveling = get(images).windowLeveling[modality][type];

            updatedWindowLeveling[modality] = {
                min: windowLeveling.min,
                max: windowLeveling.max
            };
        }

        return {
            ...state,
            currentWindowLeveling: updatedWindowLeveling
        };
    });

}