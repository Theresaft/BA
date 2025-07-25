import {writable, readable, get} from "svelte/store"
import {getBaseImagesBySegmentationIdAPI, getRawSegmentationDataAPI, getSequencesMetadataAPI} from "../lib/api"
import {removeSegmentation} from "../shared-components/viewer/segmentation"
import { UserSettings } from "./Store"
import { imagesAndSegmentationInCache } from "../shared-components/viewer/image-loader"

export let viewerState = writable({
    renderingEngine: null,
    renderingEngineId: "MY_RENDERING_ENGINE_ID",
    toolGroup: null,
    toolGroupId: "MY_TOOL_GROUP_ID",
    viewportIds: ["LEFT", "RIGHT_TOP", "RIGHT_BOTTOM"],
    voiSynchronizerId : "VOI_SYNCHRONIZER_ID",
    imageVolumeID: "",
    segmentationId: "", // Used for cornerstones segmentation volume ID (However the ID is the same as saved in out backend)
    referenceImageIds: [],
    skipOverlapping: false,
    segImageIds: [],
    currentlyDisplayedModality : "", 
    activePrimaryTool : "", // Primary Tools = left click tool
    currentWindowLeveling: {
        t1: { min: 0, max: 0 },
        t1km: { min: 0, max: 0 },
        t2: { min: 0, max: 0 },
        flair: { min: 0, max: 0 }
    },
    cameras: [], // Cornerstone camera objects for each viewport. Ordered by orientations
    orientations : ["axial", "sagittal", "coronal"],
    colormap: "Grayscale",
    colorbar : null
})

export let previewViewerState = writable({
    renderingEngine: null,
    renderingEngineId: "PREVIEW_RENDERING_ENGINE",
    toolGroup: null,
    toolGroupId: "PREVIEW_TOOL_GROUP",
    viewportIds: ["AXIAL_PREVIEW", "SAGITTAL_PREVIEW", "CORONAL_PREVIEW"],
    voiSynchronizerId : "PREVIEW_VOI_SYNCHRONIZER",
    volumeId: "",
    segmentationId: "",
    referenceImageIds: [],
    skipOverlapping: false,
    segImageIds: [],
    cameras: [], // Cornerstone camera objects for each viewport. Ordered by orientations
    orientations : ["axial", "sagittal", "coronal"]
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
        t1: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
        t1km: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
        t2: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
        flair: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
    }
})

export let previewImage = writable(null)

 
// Note: Opacity is set to 50 since it is the default for alphaFill (cornerstone), see: segmentation.config.style.getStyle()
// The segmentIndices correspond to the labels/classes of our models which are: { "background": 0, "edema": 1, "non_enhancing_and_necrosis": 2, "enhancing_tumor": 3 }
export let labelState = writable([
    { name: 'Edema', opacity: 50, isVisible: true, segmentIndex: 1 },
    { name: 'Necrotic Core', opacity: 50, isVisible: true, segmentIndex: 2 },
    { name: 'Enhancing Tumor', opacity: 50, isVisible: true, segmentIndex: 3 },
    { name: 'Test Segmentation', opacity: 50, isVisible: true, segmentIndex: 3 },
]); 

export let viewerAlreadySetup = writable(false)

export let previewViewerAlreadySetup = writable(false)

export let viewerIsLoading = writable(false);

export let imageLoadTriggerEnabled = writable(true);

export let previewViewerIsLoading = writable(false)

export let segmentationLoaded = writable(false)

export let loadCount = writable(0) // increamented each time an image is loaded to the main viewer

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

/**
 * 1) Fetches t1, t1km, t2, flair and raw segmentation array
 * 2) saves the URLs of the blobs and metadata in "images"
 * -> T1 will be loaded automatically when it is set 
 */
export async function loadImage(segmentationID, file_format) {
    try {

        const segmentationId = segmentationID.toString()

        // Clear old segmentations and images if any
        if (get(viewerState).segmentationId) {
            removeSegmentation(get(viewerState).segmentationId);

            // Reset labels
            labelState.update(labels =>
                labels.map(label => ({
                    ...label,
                    opacity: 50,
                    isVisible: true
                }))
            );

            segmentationLoaded.set(false);

            // Clear old images from store
            resetImageStore()

            // Clear old images from the viewport
            const renderingEngine = get(viewerState).renderingEngine
            
            for(const [index, viewportID] of get(viewerState).viewportIds.entries()){        
                const viewport = renderingEngine.getViewport(viewportID)
                viewport.removeAllActors()
            }
        }

        // Save (new) segmentation ID
        viewerState.update(state => ({
            ...state,
            segmentationId: segmentationId,
        }));


        viewerIsLoading.set(true);

        if(!imagesAndSegmentationInCache(segmentationId)){
            // Fetch images and segmentation data
            const baseImages = await getBaseImagesBySegmentationIdAPI(segmentationId);
            const segmentationData = await getRawSegmentationDataAPI(segmentationId);

            // Cancel when viewer is no longer in loading state (e.g. user changed page during loading)
            if(!get(viewerIsLoading)){
                resetImageStore()
                return
            }

            images.update(state => ({
                ...state,
                t1: baseImages.t1,
                t1km: baseImages.t1km,
                t2: baseImages.t2,
                flair: baseImages.flair,
                labels: segmentationData.segmentation
            }));
        }

        const baseImageMetaData = await getSequencesMetadataAPI(segmentationId);
        const windowLevelingData = baseImageMetaData["window-leveling"];

        // Save both window leveling types (minMax and dicomtag-based)
        images.update(state => ({
            ...state,
            windowLeveling: {
                ...windowLevelingData
            }
        }));

        // Reset window leveling
        if (get(UserSettings)["minMaxWindowLeveling"] || file_format === "nifti") {
            resetWindowLeveling("minMax");
        } else {
            resetWindowLeveling("dicomTag");
        }

        imageLoadTriggerEnabled.set(true)
        loadCount.update(n => n + 1);


    } catch (error) {
        console.error('Error loading image:', error);
    } 
}


export function resetImageStore(){
    images.set({
        t1: null,
        t1km: null,
        t2: null,
        flair: null,
        labels: [],
        fileType: "",
        windowLeveling: {
            t1: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
            t1km: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
            t2: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
            flair: { minMax: { min: 0, max: 0 }, dicomTag: { min: 0, max: 0 } },
        }
    });
}