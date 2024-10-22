<script>
    import Card from "../general/Card.svelte"
    import ProjectEntry from "./ProjectEntry.svelte"
    import { createEventDispatcher } from "svelte"
    
    const dispatch = createEventDispatcher()

    // TODO Get the projects list from the store
    let projects = [
        {
            projectName: "ExampleProject",
            fileType: "DICOM",
            foldersToFilesMapping: [],
            segmentations: [
                {
                    segmentationName: "MySegmentation 1",
                    sequenceMappings: [
                        { t1: "T1W_3D_tra_314" },
                        { t2: "T2_SSh_TSE_934" },
                        { t1KM: "T1W_3D_TFE_R3_KM_823" },
                        { flair: "3D_FLAIR_tra_412" },
                    ],
                    model: "Our model",
                    date: "2024-06-05T14:45:56",
                    data: null,
                },
                {
                    segmentationName: "MySegmentation 2",
                    sequenceMappings: [
                        { t1: "T1W_3D_tra_304" },
                        { t2: "T2_SSh_TSE_901" },
                        { t1KM: "T1W_3D_TFE_R3_KM_801" },
                        { flair: "3D_FLAIR_sag_401" },
                    ],
                    model: "Our model",
                    date: "2024-06-05T14:45:56",
                    data: null,
                },
            ],
        },
        {
            projectName: "Another great project",
            fileType: "NIFTI",
            foldersToFilesMapping: [],
            segmentations: [
                {
                    segmentationName: "MySegmentation",
                    sequenceMappings: [
                        { t1: "T1W_3D_tra_304" },
                        { t2: "T2_SSh_TSE_901" },
                        { t1KM: "T1W_3D_TFE_R3_KM_801" },
                        { flair: "3D_FLAIR_sag_401" },
                    ],
                    model: "Our model",
                    date: "2024-06-05T14:45:56",
                    data: null,
                },
            ],
        },
        {
            projectName: "ExampleProject",
            fileType: "Other",
            foldersToFilesMapping: [],
            segmentations: [
                {
                    segmentationName: "MySegmentation",
                    sequenceMappings: [
                        { t1: "T1W_3D_tra_304" },
                        { t2: "T2_SSh_TSE_901" },
                        { t1KM: "T1W_3D_TFE_R3_KM_801" },
                        { flair: "3D_FLAIR_sag_401" },
                    ],
                    model: "Our model",
                    date: "2024-06-05T14:45:56",
                    data: null,
                },
            ],
        },
    ];
</script>

<div class="container">
    {#each projects as project}
        <div class="project-container">
            <ProjectEntry on:createSegmentation={() => dispatch("createSegmentation")} {project}/>
        </div>
    {/each}
    <button class="button add-project-button" on:click={() => dispatch("createProject")}>Projekt hinzufügen</button>
</div>

<style>
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
