<!-- This wrapper is intended to be used by every +page.svelte of the project. The wrapper includes the navbar and footer elements.
 The content inside the page wrapper is arbitrary. It should be noted that the slot content is already contained in a main tag, meaning
 that containing it in such a tag again would be redundant and can lead to erroneous layouts. -->

 <!-- TODO: Why dont't we use +layout.svelte instead?-->
<script>
    import Navbar from "./Navbar.svelte"
    import Footer from "./Footer.svelte"
    import { onMount } from 'svelte'
    import { Projects, getProjectsFromJSONObject, hasLoadedProjectsFromBackend, isLoggedIn } from "../stores/Store"
    import { getAllProjectsAPI } from "../lib/api"

    export let removeMainSideMargin = false
    export let showFooter = true

    onMount(async () => {
        // Update login status
        $isLoggedIn = sessionStorage.getItem('session_token') !== null
        // Start Papaya Viewer globally
        window.papaya.Container.startPapaya()
        await getProjectsFromBackend()
    });

    async function getProjectsFromBackend() {
        // Get the projects if they haven't been fetched yet and if the user is logged in.
        // This prevents loading data without a session cookie and loading content several times
        // when the user switches between subpages.
        if (!$hasLoadedProjectsFromBackend && $isLoggedIn) {
            const loadedProjectData = await getAllProjectsAPI()
            $Projects = getProjectsFromJSONObject(loadedProjectData)
            $hasLoadedProjectsFromBackend = true
            console.log("Parsed projects:")
            console.log($Projects)
        }
    }
</script>

<div class="container">
    <Navbar/>
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

    /* Main takes up all remaining space at sets position to relative for child components*/
    main {
        position: relative;  /** TODO: Remove */
        flex: 1; 
    }
</style>