<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";

    let uploaderVisible = true

    const closeUploader = (e) => {
        let data = e.detail
        uploaderVisible = false
        console.log("Sent data", data)
    }
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        {#if uploaderVisible}
            <Card title="Segmentierung" center={true} dropShadow={false}>
                <p class="description">
                    Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern. Es muss aber von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden.
                </p>
                <FolderUploader on:closeUploader={closeUploader}/>
            </Card>
        {/if}
    </div>
</PageWrapper>


<style>
    .description {
        margin: 20px 0;
    }
    .uploader-wrapper {
        all: unset;
    }
</style>