<script>
    import ProjectEntry from "./ProjectEntry.svelte"
    import { createEventDispatcher } from "svelte"
    import { Projects } from "../../stores/Store"
    import { get } from "svelte/store"
    
    const dispatch = createEventDispatcher()

    let projects = get(Projects)
    let reloadProjectEntries

    function deleteProject(e) {
        const projectNameToDelete = e.detail
        const projectsToKeep = $Projects.filter(project => project.projectName !== projectNameToDelete)

        $Projects = projectsToKeep
        projects = $Projects
    }

    function deleteSegmentation(e) {
        const {projectName: projectNameTarget, segmentationName: segmentationNameToDelete} = e.detail
        console.log("Deleting segmentation")
        console.log($Projects)

        // Update the projects such that only the segmentation from the project in question is deleted.
        Projects.update(currentProjects => currentProjects.map(project => {
            if (project.projectName === projectNameTarget) {
                project.segmentations = project.segmentations.filter(segmentation => segmentation.segmentationName !== segmentationNameToDelete)
            }
            
            return project
            })
        )

        console.log($Projects)
        
        // Ensure the components are actually updated on the screen
        reloadProjectEntries = !reloadProjectEntries
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
