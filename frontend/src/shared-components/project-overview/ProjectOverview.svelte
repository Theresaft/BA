<script>
    import Card from "../general/Card.svelte";
    import ProjectEntry from "./ProjectEntry.svelte";

    // TODO Get the projects list from the store
    /**
     * This is the structure of the projects:
     * projects is a list of projects, each with a name, file type (DICOM or Nifti), folders-to-files mapping,
     * and the segmentation data. The foldersToFilesMapping is equivalent to the variable with the same name in FolderUploader.
     * segmentations is a list of segmentations that has a segmentationMappings list (which maps a sequence type to a folder name),
     * the model name, the creation date of the segmentation and the actual payload under the variable data.
     * Example:
     * [
     *  {
     *      projectName: "ExampleProject",
     *      fileType: "DICOM",
     *      foldersToFilesMapping: [],
     *      segmentations: [
     *          {
     *              sequenceMappings: [
     *                  {t1: "T1W_3D_tra_304"},
     *                  {t2: "T2_SSh_TSE_901"},
     *                  {t1Km: "T1W_3D_TFE_R3_KM_801"},
     *                  {flair: "3D_FLAIR_sag_401"},
     *              ],
     *              model: "Our model",
     *              date: "2024-06-05T14:45:56",
     *              data: null,
     *          },
     *      ],
     *  },
     * ]
     */
    let projects = [
        {
            projectName: "ExampleProject",
            fileType: "DICOM",
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
    { #each projects as project }
        <div class="project-container">
            <ProjectEntry {project}/>
        </div>
    {/each}
</div>

<style>

</style>
