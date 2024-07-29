<script>
    import Navbar from "../../single-components/Navbar.svelte";
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FileUploader from "../../shared-components/FileUploader.svelte";
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        <Card title="Segmentierung" center={true} dropShadow={false}>
            <FileUploader/>
            Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt, die Sie aber danach noch ändern können.
        </Card>
    </div>
</PageWrapper>


<style>

</style>