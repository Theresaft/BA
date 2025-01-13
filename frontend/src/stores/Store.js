import {writable, readable, get} from "svelte/store"
import { Project } from "./Project.js"
import { Segmentation, SegmentationStatus } from "./Segmentation.js"
import { Sequence, DicomSequence, NiftiSequence } from "./Sequence.js"
import { getSegmentationStatusAPI } from '../lib/api.js';


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

// Updates the segmentation status (triggers reactivity)
export function updateSegmentationStatus(segmentationID, newStatus) {
    Projects.update(projects => {
        // Map through the projects array to find the correct segmentation and update it
        return projects.map(project => {
            // Check if the project contains the segmentation
            const updatedSegmentations = project.segmentations.map(segmentation => {
                if (segmentation.segmentationID === segmentationID) {
                    // Update the status of the matching segmentation
                    return {
                        ...segmentation,
                        status: SegmentationStatus[newStatus]
                    };
                }
                // Return the unchanged segmentation if it doesn't match
                return segmentation;
            });

            // Return the updated project with the updated segmentations
            return {
                ...project,
                segmentations: updatedSegmentations
            };
        });
    });
}


// Starts a single Segmentation polling
export function pollSegmentationStatus(segmentationID, pollInterval = 1000) {
    return new Promise((resolve, reject) => {
        let latestStatus = ""

        const pollingInterval = setInterval(async () => {
            try {
                const status = await getSegmentationStatusAPI(segmentationID);

                // Check if status has changed
                if(latestStatus !== status){
                    updateSegmentationStatus(segmentationID, status)
                    latestStatus = status
                }

                if(status === "DONE"){
                    clearInterval(pollingInterval); 
                    resolve({ status }); 
                } else if (status === "ERROR"){
                    clearInterval(pollingInterval); 
                    reject(new Error("Segmentation process failed.")); 
                }
            } catch (error) {
                clearInterval(pollingInterval); 
                reject(error); 
            }
        }, pollInterval);

    });
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Starts polling routine for all ongoing segmentations (round-robin)
export async function startPolling(){
    isPolling.set(true)  
    const segmentationIDsToPoll = []

    // Retrieve all ongoing segmentations
    for(const project of get(Projects) ){
        for(const segmentation of project.segmentations){    
            if(segmentation.status.id === "QUEUEING" || segmentation.status.id === "PREPROCESSING" || segmentation.status.id === "PREDICTING" ){
                segmentationIDsToPoll.push(segmentation.segmentationID)
            }
        }
    }

    // Start polling routine for each ongoing segmentation (scaled)
    for(const segmentationID of segmentationIDsToPoll){
        console.log("Start polling for segmentationID: " + segmentationID);
        pollSegmentationStatus(segmentationID, segmentationIDsToPoll.length * 1000)
        await delay(1000);
    }
}