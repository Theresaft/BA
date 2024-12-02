<script>
    import ProjectEntry from "./ProjectEntry.svelte"
    import { createEventDispatcher, onMount } from "svelte"
    import { Projects, RecentSegmentations, hasLoadedProjectsFromBackend } from "../../stores/Store"
    import { get } from "svelte/store"
    
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


    function deleteProject(e) {
        const projectNameToDelete = e.detail
        const projectsToKeep = $Projects.filter(project => project.projectName !== projectNameToDelete)

        $Projects = projectsToKeep
        projects = $Projects

        // Since the deletion of a project also affects the recent segmentations, update the recent segmentations
        // store variable.
        $RecentSegmentations = $RecentSegmentations.filter(recentSegmentation => recentSegmentation.projectName !== projectNameToDelete)
    }

    function deleteSegmentation(e) {
        const {projectName: projectNameTarget, segmentationName: segmentationNameToDelete} = e.detail

        // Update the projects such that only the segmentation from the project in question is deleted.
        Projects.update(currentProjects => currentProjects.map(project => {
                if (project.projectName === projectNameTarget) {
                    project.segmentations = project.segmentations.filter(segmentation => segmentation.segmentationName !== segmentationNameToDelete)
                }
                
                return project
            })
        )

        // Ensure the components are actually updated on the screen
        reloadProjectEntries = !reloadProjectEntries

        $RecentSegmentations = $RecentSegmentations.filter(recentSegmentation => recentSegmentation.segmentationName !== segmentationNameToDelete)
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
