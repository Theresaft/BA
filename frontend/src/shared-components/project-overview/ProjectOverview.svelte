<script>
    import ProjectEntry from "./ProjectEntry.svelte"
    import { createEventDispatcher } from "svelte"
    import { Projects } from "../../stores/Store"
    import { get } from "svelte/store"
    
    const dispatch = createEventDispatcher()

    let projects = get(Projects)

    function deleteProject(e) {
        const projectNameToDelete = e.detail
        const projectsToKeep = $Projects.filter(project => project.projectName !== projectNameToDelete)

        $Projects = projectsToKeep
        projects = $Projects
    }
</script>

<div class="container">
    {#if projects.length === 0}
        <p class="no-projects-text">
            Es sind noch keine Projekte vorhanden.
        </p>
    {/if}
    {#each projects as project}
        <div class="project-container">
            <ProjectEntry on:delete={deleteProject} on:createSegmentation={() => dispatch("createSegmentation", project)} {project}/>
        </div>
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
