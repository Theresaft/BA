<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";

    const processUploadedFolders = () => {
        console.log("Pressed done button")
    }
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        <Card title="Segmentierung" center={true} dropShadow={false} doneCallback={() => {processUploadedFolders()}}>
            <p class="description">
                Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern.
            </p>
            <FolderUploader/>
        </Card>
    </div>
</PageWrapper>


<style>
    .description {
        margin-bottom: 20px;
    }
</style>