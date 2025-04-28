import {writable, readable, get} from "svelte/store"
import { Project } from "./Project.js"
import { Segmentation, SegmentationStatus } from "./Segmentation.js"
import { Sequence, DicomSequence, NiftiSequence } from "./Sequence.js"
import { getAllSegmentationStatusesAPI } from '../lib/api.js'


export const AvailableModels = [
    {
        id: "nnunet-model:brainns",
        displayName: "nn-Unet",
        description: "Ein vortrainiertes KI-Modell, das zwischen keinem Tumor und drei Tumorgewebe-Typen unterscheidet."
    },
    {
        id: "own-model:brainns",
        displayName: "Eigenes Modell",
        description: "Ein selbst trainiertes KI-Modell, das zwischen keinem Tumor und drei Tumorgewebe-Typen unterscheidet."
    }
    // Not supported yet!
    // {
    //     id: "deepmedic-model:brainns",
    //     displayName: "deepMedic",
    //     description: "Ein vortrainiertes KI-Modell, das zwischen Tumor/keinem Tumor unterscheidet."
    // },
]

// A list of projects of type Project. These are globally available for the currently logged in user. Upon login or reloading of the page,
// the Projects list will always be updated with data from the backend. When a segmentation or project is added to the user data, we have to
// add an element to the corresponding list in Projects or the segmentations list in the project that was extended by a new segmentation.
// Another use case when the projects list may be updated is when a segmentation changes its status, e.g., from queueing to preprocessing.
export let Projects = writable([])

// Holds track if the user is logged in 
export let isLoggedIn = writable(false)

// Flag that indicates if polling for ongoing segmentations has already been started
// Prevent polling again page change or relogin
export let isPolling = writable(false)

// Whether projects have been loaded from the backend already. Necessary because onMount is too stupid to distinguish between reload of a page
// and refresh.
export let hasLoadedProjectsFromBackend = writable(false)

// For now, use a Store variable to store whether to show deletion popups.
// This variable refers to the deletion of a single entry. The modal for deleting all entries can't be skipped.
// TODO Do this using cookies
export let ShowNoDeleteModals = writable(false)

// A constant list of strings of possible sequences to display to the user.
export let SequenceDisplayStrings = readable(["T1-KM", "T1", "T2/T2*", "Flair"])

// These are the user settings from the backend. In case we can't load the user settings, we set default values
// here.
export let UserSettings = writable({
    "confirmDeleteEntry" : true,
    "numberDisplayedRecentSegmentations" : 1000000,
    "defaultDownloadType" : "nifti",
    "minMaxWindowLeveling" : false // Default: Window Leveling based on DICOM tags. If true: Use min/max pixel value instead
})

// The number of milliseconds between each request for the status of the segmentations.
export const StatusPollingIntervalMs = 1000 * 5

// Symbols that can't be used in project or segmentation names.
export const InvalidSymbolsInNames = [" ", "/", "\\", ":", "*", "?", "\"", "<", ">", "|", "`", "."]



/**
 * Given a list of elements allowed symbols to show, display these elements properly. For example, whitespace is shown as the
 * string "Leerzeichen" instead of just printing a whitespace, and the last two words are properly separated by "und".
 */
export function formatAllowedSmyoblList(list) {
    // Handle the case where the array is empty
    if (list.length === 0) {
        return ""
    }
    
    // Handle the case where the array has only one item
    if (list.length === 1) {
        return list[0]
    }

    list = list.map(el => el === " " ? "Leerzeichen" : el)
    
    // Get all items except the last one
    const allExceptLast = list.slice(0, -1).join(', ')
    // Get the last item
    const lastItem = list[list.length - 1]
    
    // Combine all items with 'und' before the last one
    return `${allExceptLast} und ${lastItem}`
}


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
                const sequence = (project.fileType === "dicom") ? new DicomSequence() : (project.fileType === "nifti") ? new NiftiSequence() : new Sequence()
                sequence.sequenceID = sequenceData.sequenceID || -1
                sequence.acquisitionPlane = sequenceData.acquisitionPlane || ""
                sequence.resolution = sequenceData.resolution || 0.0
                sequence.sizeInBytes = sequenceData.sizeInBytes || 0
                sequence.selected = sequenceData.selected || false
                sequence.sequenceType = sequenceData.sequenceType || ""
                sequence.classifiedSequenceType = sequenceData.classifiedSequenceType || ""
                switch (project.fileType) {
                    case "dicom" : {
                        sequence.folder = sequenceData.sequenceName || ""
                        sequence.fileNames = Array.isArray(sequenceData.fileNames) ? sequenceData.fileNames : []
                        sequence.files = Array.isArray(sequenceData.files) ? sequenceData.files : []
                        break
                    }
                    case "nifti" : {
                        sequence.fileName = sequenceData.sequenceName || ""
                        sequence.file = null
                    }
                }

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
                segmentation.status = SegmentationStatus[segmentationData.status]
                segmentation.projectName = project.projectName
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

// Updates the segmentation status of all segmentations in segmentationIDsToStatuses (triggers reactivity)
export function updateSegmentationStatus(segmentationIDsToStatuses) {
    Projects.update(projects => {
        // Map through the projects array to find the correct segmentation and update it
        return projects.map(project => {
            // Check if the project contains the segmentation
            const updatedSegmentations = project.segmentations.map(segmentation => {
                // Check if the segmentation ID is in the map passed as an argument
                if (segmentation.segmentationID in segmentationIDsToStatuses) {
                    const statusString = segmentationIDsToStatuses[segmentation.segmentationID]
                    // Update the status of the matching segmentation
                    return {
                        ...segmentation,
                        status: SegmentationStatus[statusString]
                    }
                }
                // Return the unchanged segmentation if it doesn't match
                return segmentation
            })

            // Return the updated project with the updated segmentations
            return {
                ...project,
                segmentations: updatedSegmentations
            }
        })
    })
}


let pollingInterval;

// Starts polling routine for all ongoing segmentations
export async function startPolling() {
    // Set isPolling flag to true so that no incorrect calls to this function are done
    isPolling.set(true);

    // Check if there is any segmentation with the relevant statuses
    const shouldStartPolling = get(Projects).some(project => 
        project.segmentations.some(segmentation => 
            ["QUEUEING", "PREPROCESSING", "PREDICTING"].includes(segmentation.status.id)
        )
    );
    
    // Only start polling if such a segmentation exists
    if (shouldStartPolling) {
        pollSegmentationStatuses(StatusPollingIntervalMs);
    } else {
        isPolling.set(false); 
    }
}

export async function stopPolling() {
    isPolling.set(false)
    clearInterval(pollingInterval)
}


/**
 * This starts polling data for all segmentations at once in a given interval.
 * @param {The polling interval in milliseconds} pollIntervalMs 
 * @returns The corresponding promise
 */
export function pollSegmentationStatuses(pollIntervalMs) {
    return new Promise((resolve, reject) => {
        pollingInterval = setInterval(async () => {
            try {
                const result = await getAllSegmentationStatusesAPI();
                if (!result.ok) {
                    throw new Error("Fetching segmentation statuses failed");
                }

                const segmentationStatuses = await result.json();
                updateSegmentationStatus(segmentationStatuses);

                // Check if there are still ongoing segmentations
                const hasOngoingSegmentations = get(Projects).some(project =>
                    project.segmentations.some(segmentation =>
                        ["QUEUEING", "PREPROCESSING", "PREDICTING"].includes(segmentation.status.id)
                    )
                );

                // Stop polling when no more ongoing segmentations
                if (!hasOngoingSegmentations) {
                    stopPolling();
                    resolve({});
                }

            } catch (error) {
                stopPolling();
                reject(error);
            }
        }, pollIntervalMs);
    });
}