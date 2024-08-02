import {writable, readable} from "svelte/store"

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
    QUEUEING: "In Warteschlange",
    PENDING: "Ausstehend",
    DONE: "Fertig",
    CANCELED: "Abgebrochen",
    ERROR: "Fehler"
})

// In RecentSegmentations, we store the segmentation name, the folder names, corresponding sequences, time of scheduling, and status
// of the segmentation.
/**
 * [
 *  {
 *  segmentationName: "Patient_02082024_Jack_Petersen",
 *  folderMapping: [
 *      {folder: ..., files: ..., sequences: ..., ...}
 *  ],
 *  scheduleTime: "02-08-2024T02:07", (UTC timestamp)
 *  segmentationStatus: SegmentationStatus.PENDING
 *  }
 * ]
 */

export let RecentSegmentations = writable([])

export default NavbarObjects