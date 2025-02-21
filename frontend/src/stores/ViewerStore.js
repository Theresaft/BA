import {writable, readable, get} from "svelte/store"

export let viewerState = writable({
    renderingEngine: null,
    renderingEngineId: "MY_RENDERING_ENGINE_ID",
    toolGroup: null,
    toolGroupId: "MY_TOOL_GROUP_ID",
    viewportIds: ["CT_AXIAL", "CT_SAGITTAL", "CT_CORONAL"],
    volumeId: "",
    segmentationId: "",
    referenceImageIds: [],
    skipOverlapping: false,
    segImageIds: [],
})

export let viewerAlreadySetup = writable(false)


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
})

export let viewerIsLoading = writable(false);

export let toolState = writable({
    brushIsActive: false
})