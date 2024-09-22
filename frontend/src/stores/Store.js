import {writable, readable, get} from "svelte/store"

// The positions are encoded as a JS enum. Within a position, e.g., CENTER, the navbar elements
// below will be listed in the same order they are shown here.
export const NavbarPosition = readable({
    LEFT: "left",
    CENTER: "center",
    RIGHT: "right"
});

// The store elements are only readable.
// The display image path is relative to the shared-components/ folder.
const NavbarObjects = readable([
    {
        displayName: "",
        route: "/",
        shownBeforeLogin: true,
        shownAfterLogin: true,
        displayPosition: get(NavbarPosition).LEFT,
        highlightWhenSelected: false,
        displayImage: "svg/UniLogo.svg"
    },
    {
        displayName: "Start",
        route: "/",
        shownBeforeLogin: true,
        shownAfterLogin: true,
        displayPosition: get(NavbarPosition).CENTER,
        highlightWhenSelected: true,
        displayImage: null
    },
    {
        displayName: "Segmentierung",
        route: "/segmentation",
        shownBeforeLogin: false,
        shownAfterLogin: true,
        displayPosition: get(NavbarPosition).CENTER,
        highlightWhenSelected: true,
        displayImage: null
    },
    {
        displayName: "Viewer",
        route: "/viewer",
        shownBeforeLogin: false,
        shownAfterLogin: true,
        displayPosition: get(NavbarPosition).CENTER,
        highlightWhenSelected: true,
        displayImage: null
    },
    {
        displayName: "Info",
        route: "/info",
        shownBeforeLogin: true,
        shownAfterLogin: true,
        displayPosition: get(NavbarPosition).CENTER,
        highlightWhenSelected: true,
        displayImage: null
    },
    {
        displayName: "",
        route: "/settings",
        shownBeforeLogin: false,
        shownAfterLogin: true,
        displayPosition: get(NavbarPosition).RIGHT,
        highlightWhenSelected: true,
        displayImage: "svg/SettingsSymbol.svg"
    },
])

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
    QUEUEING: {id: "queueing", displayName: "In Warteschlange", svgPath: ""},
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
        segmentationName: "Patient_02381274_Jan_Petersen",
        folderMapping: [
            {}
        ],
        scheduleTime: "02-08-2024T02:07",
        segmentationStatus: get(SegmentationStatus).DONE,
        segmentationResult: null,
        id:"0e81fb9e-4bbe-4d98-9899-35380c0d2012"
     },
     {
         segmentationName: "Patient_234781237_Sandra_Mueller",
         folderMapping: [
             {}
         ],
         scheduleTime: "05-08-2024T14:07",
         segmentationStatus: get(SegmentationStatus).DONE,
         segmentationResult: null,
         id:"3aabda7a-f942-41fb-a199-26fadf1fc1af"
      },
      {
        segmentationName: "Patient_2348538747_Laura_Schiller",
        folderMapping: [
            {}
        ],
        scheduleTime: "05-08-2024T14:07",
        segmentationStatus: get(SegmentationStatus).DONE,
        segmentationResult: null,
        id:"3aabda7a-f942-41fb-a199-26fadf1fc1af"
     },
     {
        segmentationName: "Patient_773623647_Olaf_Scholz",
        folderMapping: [
            {}
        ],
        scheduleTime: "05-08-2024T14:07",
        segmentationStatus: get(SegmentationStatus).DONE,
        segmentationResult: null,
        id:"3aabda7a-f942-41fb-a199-26fadf1fc1af"
     },
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

export function deleteSegmentation(segmentationName) {
    RecentSegmentations.update(currentSegmentations => {
        return currentSegmentations.filter(seg => seg.segmentationName !== segmentationName)
    })
}

export default NavbarObjects