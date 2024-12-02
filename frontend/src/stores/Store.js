import {writable, readable, get} from "svelte/store"
import { Project } from "./Project.js"
import { Segmentation } from "./Segmentation.js"
import { Sequence } from "./Sequence.js"


// The positions are encoded as a JS enum. Within a position, e.g., CENTER, the navbar elements
// below will be listed in the same order they are shown here.
export const NavbarPosition = readable({
    LEFT: "left",
    CENTER: "center",
    RIGHT: "right"
})

export const AvailableModels = [
    {
        id: "nnunet-model:brainns",
        displayName: "nn-Unet",
        description: "Ein vortrainiertes KI-Modell, das zwischen Tumor/keinem Tumor unterscheidet."
    },
    {
        id: "deepmedic-model:brainns",
        displayName: "deepMedic",
        description: "Ein vortrainiertes KI-Modell, das zwischen Tumor/keinem Tumor unterscheidet."
    },
    {
        id: "own",
        displayName: "Eigenes Modell",
        description: "Ein selbst trainiertes KI-Modell, das zwischen keinem Tumor und drei Tumorgewebe-Typen unterscheidet."
    }
]

export const SegmentationStatus = readable({
    QUEUEING: {id: "QUEUEING", displayName: "In Warteschlange", svgPath: ""},
    PREPROCESSING: {id: "PREPROCESSING", displayName: "Preprocessing", svgPath: ""},
    PREDICTING: {id: "PREDICTING", displayName: "Vorhersage", svgPath: ""},
    DOESNT_EXIST: {id: "DOESNT-EXIST", displayName: "Fehler", svgPath: ""},
    DONE: {id: "DONE", displayName: "Fertig", svgPath: ""},
})

// A list of projects of type Project. These are globally available for the currently logged in user. Upon login or reloading of the page,
// the Projects list will always be updated with data from the backend. When a segmentation or project is added to the user data, we have to
// add an element to the corresponding list in Projects or the segmentations list in the project that was extended by a new segmentation.
// Another use case when the projects list may be updated is when a segmentation changes its status, e.g., from queueing to preprocessing.
export let Projects = writable([])

// Holds track if the user is logged in 
export let isLoggedIn = writable(false)

// Whether projects have been loaded from the backend already. Necessary because onMount is too stupid to distinguish between reload of a page
// and refresh.
export let hasLoadedProjectsFromBackend = writable(false)

// For now, use a Store variable to store whether to show deletion popups.
// This variable refers to the deletion of a single entry. The modal for deleting all entries can't be skipped.
// TODO Do this using cookies
export let ShowNoDeleteModals = writable(false)

// In RecentSegmentations, we store the segmentation name, the folder names, corresponding sequences, time of scheduling, and status
// of the segmentation.
export let RecentSegmentations = writable([])

/**
 * Given a JSON object from the backend, set the Project object data from the given JSON data.
 */
export function getProjectsFromJSONObject(jsonObject) {

    // Delete possibly existing projects in the store
    const allProjects = []

    for (let jsonProject of jsonObject) {
        const project = new Project()
        project.projectID = jsonProject.projectID || -1
        project.projectName = jsonProject.projectName || ""
        project.fileType = jsonProject.fileType || "dicom"
    
        // Parse sequences
        if (Array.isArray(jsonProject.sequences)) {
            project.sequences = jsonProject.sequences.map(sequenceData => {
                const sequence = new Sequence()
                sequence.sequenceID = sequenceData.sequenceID || -1
                sequence.folder = sequenceData.sequenceName || ""
                sequence.acquisitionPlane = sequenceData.acquisitionPlane || ""
                sequence.fileNames = Array.isArray(sequenceData.fileNames) ? sequenceData.fileNames : []
                sequence.files = Array.isArray(sequenceData.files) ? sequenceData.files : []
                sequence.resolution = sequenceData.resolution || 0.0
                sequence.selected = sequenceData.selected || false
                sequence.sequenceType = sequenceData.sequenceType || ""
                sequence.classifiedSequenceType = sequenceData.classifiedSequenceType || ""
                return sequence
            })
        }

        // Parse segmentations
        if (Array.isArray(jsonProject.segmentations)) {
            project.segmentations = jsonProject.segmentations.map(segmentationData => {
                const segmentation = new Segmentation()
                segmentation.segmentationID = segmentationData.segmentationID || -1
                segmentation.segmentationName = segmentationData.segmentationName || ""
                segmentation.dateTime = segmentationData.dateTime || ""
                segmentation.model = segmentationData.model || ""
                // Match the sequence objects from above using the sequence IDs
                segmentation.selectedSequences = {
                    flair: project.sequences.find(seq => seq?.sequenceID === segmentationData?.flairSequence),
                    t1: project.sequences.find(seq => seq?.sequenceID === segmentationData?.t1Sequence),
                    t1km: project.sequences.find(seq => seq?.sequenceID === segmentationData?.t1kmSequence),
                    t2: project.sequences.find(seq => seq?.sequenceID === segmentationData?.t2Sequence)
                }
                segmentation.data = segmentationData.data || null
                return segmentation
            })
        }
        
        allProjects.push(project)
    }

    return allProjects
}

export function updateSegmentationStatus(segmentationName, newStatus) {
    RecentSegmentations.update(currentSegmentations => {
        return currentSegmentations.map(seg => {
            if (seg.segmentationName === segmentationName) {
                return {...seg, segmentationStatus: newStatus}
            } else {
                return seg
            }
        })
    })
}

export function deleteSegmentation(segmentationName) {
    RecentSegmentations.update(currentSegmentations => {
        return currentSegmentations.filter(seg => seg.segmentationName !== segmentationName)
    })
}
