<script>
    import ProjectEntry from "./ProjectEntry.svelte"
    import { createEventDispatcher, onMount } from "svelte"
    import { Projects, RecentSegmentations, hasLoadedProjectsFromBackend } from "../../stores/Store"
    import { get } from "svelte/store"
    import { deleteProjectAPI, deleteSegmentationAPI } from "../../lib/api.js"
    
    const dispatch = createEventDispatcher()

    let projects = get(Projects)
    let reloadProjectEntries

    // Set the initial scroll position to 0 on creation of this page
    onMount(() => {
        window.scrollTo({top: 0})
    })

    // Reload the projects when they have been fetched from the backend
    $: {
        if ($hasLoadedProjectsFromBackend) {
            projects = get(Projects)
        }
    }

    /**
     * Delete the project stored in the event e from the $Projects variable and send a delete request to the backend.
     * If the deletion succeeds, actually delete the project in the $Project from the store. If it doesn't succeed, don't
     * change $Project and show an error modal to the user.
     * @param e
     */
    async function deleteProject(e) {
        const projectIDToDelete = e.detail
        // Send the delete request to the backend
        const response = await deleteProjectAPI(projectIDToDelete)

        // Only update the frontend Store variables if the response is positive.
        if (response.ok) {
            console.log("Deleting project successful")
            const projectsToKeep = $Projects.filter(project => project.projectID !== projectIDToDelete)

            $Projects = projectsToKeep
            projects = $Projects

            // Since the deletion of a project also affects the recent segmentations, update the recent segmentations
            // store variable.
            $RecentSegmentations = $RecentSegmentations.filter(recentSegmentation => recentSegmentation.projectID !== projectIDToDelete)
        } else {
            // TODO Show error modal
            console.error('Fehler bei der Anfrage:', response.statusText)
        }
    }

    /**
     * Given a segmentation ID in the event details, try to delete the segmentation in the database. If that succeeds, also update
     * the $Projects variable in the frontend.
     * @param e
     */
    async function deleteSegmentation(e) {
        const {projectName: projectName, segmentationName: segmentationName, segmentationID: segmentationID} = e.detail
        
        const response = await deleteSegmentationAPI(segmentationID)

        if (response.ok) {
            // Update the projects such that only the segmentation from the project in question is deleted.
            Projects.update(currentProjects => currentProjects.map(project => {
                    if (project.projectName === projectName) {
                        project.segmentations = project.segmentations.filter(segmentation => segmentation.segmentationID !== segmentationID)
                    }
                    
                    return project
                })
            )

            // Ensure the components are actually updated on the screen
            reloadProjectEntries = !reloadProjectEntries

            $RecentSegmentations = $RecentSegmentations.filter(recentSegmentation => recentSegmentation.segmentationID !== segmentationID)
        } else {
            // TODO Show error modal
            console.error('Fehler bei der Anfrage:', response.statusText)
        }
    }
</script>

<div class="container">
    {#if projects.length === 0}
        <p class="no-projects-text">
            Es sind noch keine Projekte vorhanden.
        </p>
    {/if}
    {#each projects as project}
        {#key reloadProjectEntries}
            <div class="project-container">
                <ProjectEntry on:delete={deleteProject} on:deleteSegmentation={deleteSegmentation} on:createSegmentation={() => dispatch("createSegmentation", project)} {project}/>
            </div>
        {/key}
    {/each}
    <button class="button add-project-button" on:click={() => dispatch("createProject")}>Projekt hinzufügen</button>
</div>

<style>
    .no-projects-text {
        margin-left: 7px;
    }
    .add-project-button {
        width: 100%;
        padding-top: 18px;
        padding-bottom: 18px;
        margin-top: 30px;
        font-size: 17px;
        background: var(--background-color-card-tertiary);
        color: var(--button-text-color-secondary);
    }
    .add-project-button:hover {
        background: var(--background-color-card-tertiary-hover);
        color: var(--button-text-color-primary);
    }
</style>
