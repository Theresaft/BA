<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import Card from "../../shared-components/Card.svelte";
    import FolderUploader from "../../shared-components/FolderUploader.svelte";
    import FolderSummary from "../../shared-components/FolderSummary.svelte";
    import ModelSelector from "../../shared-components/ModelSelector.svelte";

    let uploaderVisible = true
    let overviewVisible = false
    let selectedData = []

    const closeUploader = (e) => {
        let data = e.detail
        uploaderVisible = false
        console.log("Sent data", data)
        
        // TODO Send API request to get the DICOM sequences with the best resolution.
        selectedData = getSelectedData(data)
        
        console.log("Selected data", data)
        overviewVisible = true
    }

    const getSelectedData = (data) => {
        return data
    }
</script>


<PageWrapper>
    <div>
        <h1>Segmentierung</h1>
        {#if uploaderVisible}
            <Card title="Ordnerauswahl für die Segmentierung" center={true} dropShadow={false}>
                <p class="description">
                    Bitte laden Sie den gesamten Ordner mit allen DICOM-Sequenzen für den Patienten hoch. Danach werden die passenden DICOM-Sequenzen automatisch ausgewählt. Diese Auswahl können Sie danach aber noch ändern. Es muss aber von jeder Sequenz <strong>mindestens ein Ordner</strong> ausgewählt werden.
                </p>
                <FolderUploader on:closeUploader={closeUploader}/>
            </Card>
        {:else if overviewVisible}
            <Card>
                <Card title="Übersicht" center={true} dropShadow={false}>
                    <p class="description">
                        Dies sind die ausgewählten DICOM-Sequenzen:
                    </p>
                    <FolderSummary data={selectedData}/>
                    <ModelSelector/>
                </Card>
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