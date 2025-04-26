<!-- This wrapper is intended to be used by every +page.svelte of the project. The wrapper includes the navbar and footer elements.
 The content inside the page wrapper is arbitrary. It should be noted that the slot content is already contained in a main tag, meaning
 that containing it in such a tag again would be redundant and can lead to erroneous layouts. -->
<script>
    import Navbar from "./Navbar.svelte"
    import Footer from "./Footer.svelte"
    import { onMount } from 'svelte'
    import { Projects, getProjectsFromJSONObject, hasLoadedProjectsFromBackend, isLoggedIn, startPolling, isPolling, UserSettings } from "../stores/Store"
    import { getAllProjectsAPI, getSettingsAPI } from "../lib/api"

    export let hasUnsavedChanges = false
    export let removeMainSideMargin = false
    export let showFooter = true
    export let loadSettings = true

    onMount(async () => {
        try {
            // Update login status
            $isLoggedIn = sessionStorage.getItem('session_token') !== null
            await getProjectsFromBackend()
            if (loadSettings) {
                await getSettings()
            }

            // Start polling segmentation status if it's not being done yet
            if (!$isPolling && $isLoggedIn){
                startPolling()
            }
        } catch(error) {
            console.log(error)
        }
    });



    async function getProjectsFromBackend() {
        // Get the projects if they haven't been fetched yet and if the user is logged in.
        // This prevents loading data without a session cookie and loading content several times
        // when the user switches between subpages.
        if (!$hasLoadedProjectsFromBackend && $isLoggedIn) {
            const loadedProjectData = await getAllProjectsAPI()
            $Projects = getProjectsFromJSONObject(loadedProjectData)
            $hasLoadedProjectsFromBackend = true
        }
    }


    async function getSettings() {
        // Load settings
        const response = await getSettingsAPI()
        if (response.ok) {
            const data = await response.json()
            // Update store variable
            $UserSettings = data
            console.log(data)
        } else {
            throw new Error("Response from settings API not ok")
        }
    }
</script>

<div class="container">
    <Navbar {hasUnsavedChanges}/>
    <main class:remove-main-side-margin={removeMainSideMargin}>
        <slot>

        </slot>
    </main>
    {#if showFooter}
        <Footer/> 
    {/if}
</div>

<style>
    main {
        margin-top: var(--margin-main-top);
        margin-left: var(--margin-main-left-right);
        margin-right: var(--margin-main-left-right);
    }
    .remove-main-side-margin {
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
    }
    .container {
        display: flex;
        flex-direction: column; 
        min-height: 100vh;
    }
    .container::-webkit-scrollbar {
        display: none;
    }

    /* Main takes up all remaining space at sets position to relative for child components*/
    main {
        position: relative;
        flex: 1; 
    }
</style>