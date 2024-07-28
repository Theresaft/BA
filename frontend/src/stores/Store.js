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

export default NavbarObjects