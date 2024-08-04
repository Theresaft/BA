import {writable, readable, get} from "svelte/store"

// The store elements are only readable.
const NavbarObjects = readable([
    {
        displayName: "Start",
        route: "/",
        shownBeforeLogin: true,
        showAfterLogin: true,
        displayImage: null
    },
    {
        displayName: "Segmentierung",
        route: "/segmentation",
        shownBeforeLogin: false,
        showAfterLogin: true,
        displayImage: null
    },
    {
        displayName: "Viewer",
        route: "/viewer",
        shownBeforeLogin: false,
        showAfterLogin: true,
        displayImage: null
    },
    {
        displayName: "Info",
        route: "/info",
        shownBeforeLogin: true,
        showAfterLogin: true,
        displayImage: null
    },
])

export let SelectedRoute = writable("/")
export let AvailableModels = [
    {
        id: "nnunet",
        displayName: "nn-Unet",
        description: "Ein vortrainiertes KI-Modell, das zwischen Tumor/keinem Tumor unterscheidet."
    },
    {
        id: "own",
        displayName: "Eigenes Modell",
        description: "Ein selbst trainiertes KI-Modell, das zwischen keinem Tumor und drei Tumorgewebe-Typen unterscheidet."
    }
]

export const SegmentationStatus = readable({
    QUEUEING: {id: "queuing", displayName: "In Warteschlange", svgPath: ""},
    PENDING: {id: "pending", displayName: "Ausstehend", svgPath: ""},
    DONE: {id: "done", displayName: "Fertig", svgPath: ""},
    CANCELED: {id: "canceled", displayName: "Abgebrochen", svgPath: ""},
    ERROR: {id: "error", displayName: "Fehler", svgPath: ""}
})

// In RecentSegmentations, we store the segmentation name, the folder names, corresponding sequences, time of scheduling, and status
// of the segmentation.

// TODO Add randomly generated ID and use it for the update function
export let RecentSegmentations = writable([
    {
       segmentationName: "DICOM/Patient_02082024_Jack_Petersen/aaaaaaaaaaaa",
       folderMapping: [
           {}
       ],
       scheduleTime: "02-08-2024T02:07",
       segmentationStatus: get(SegmentationStatus).PENDING,
       segmentationResult: null
    }
])

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

console.log(get(SegmentationStatus))

export default NavbarObjects