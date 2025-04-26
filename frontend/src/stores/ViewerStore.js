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
    currentlyDisplayedModality : "" 
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
    segImageIds: []
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
    maxPixelValueT1 : null, 
    maxPixelValueT1km : null, 
    maxPixelValueT2 : null, 
    maxPixelValueFlair : null, 
})

export let previewImage = writable(null)

 
// Note: Opacity is set to 50 since it is the default for alphaFill (cornerstone), see: segmentation.config.style.getStyle()
export let labelState = writable([
    { name: 'Necrotic Core', opacity: 50, isVisible: true, segmentIndex: 1 },
    { name: 'Enhancing Tumor', opacity: 50, isVisible: true, segmentIndex: 2 },
    { name: 'Edema', opacity: 50, isVisible: true, segmentIndex: 3 }
]); 

export let viewerAlreadySetup = writable(false)

export let previewViewerAlreadySetup = writable(false)

export let viewerIsLoading = writable(false);

export let segmentationLoaded = writable(false)