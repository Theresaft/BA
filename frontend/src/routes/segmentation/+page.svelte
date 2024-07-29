<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        <Card title="Segmentierung" center={true} dropShadow={false}>
            <FolderUploader/>
            Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern.
        </Card>
    </div>
</PageWrapper>


<style>

</style>