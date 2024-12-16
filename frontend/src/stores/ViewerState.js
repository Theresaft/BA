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