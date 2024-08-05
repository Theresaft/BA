<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import PapayaViewer from "../../single-components/PapayaViewer.svelte";
    import Card from "../../shared-components/general/Card.svelte";
    import SearchBar from "../../shared-components/general/SearchBar.svelte";
    import RecentSegmentationsViewerEntry from "../../shared-components/recent-segmentations-viewer/RecentSegmentationsViewerEntry.svelte"
    import { RecentSegmentations, deleteSegmentation } from "../../stores/Store.js"
    import Modal from "../../shared-components/general/Modal.svelte";
    import ArrowDownSymbol from "../../shared-components/svg/ArrowDownSymbol.svelte";

    let prompt = ""
    let showModal = false
    let segmentationToDelete = {}

    $: {
        console.log(prompt)
    }

    $: noSegmentationsToShow = () => {
        console.log("bla:", $RecentSegmentations.filter(obj => obj.segmentationStatus.id === "done"))
        return $RecentSegmentations.filter(obj => obj.segmentationStatus.id === "done").length === 0
    }

    const showDeleteModal = (e) => {
        showModal = true
        segmentationToDelete = e.detail
    }

    const deleteClicked = () => {
        deleteSegmentation(segmentationToDelete.segmentationName)
        segmentationToDelete = {}
    }
</script>

<PageWrapper removeMainSideMargin={true}>
    <div class="container">
        <div class="side-card">
            <Card title="Letzte Segmentierungen" center={true} dropShadow={false} borderRadius={false}>
                <SearchBar bind:prompt={prompt}/>
                {#each $RecentSegmentations as segmentation}
                    {#if segmentation.segmentationStatus.id === "done"}
                        <RecentSegmentationsViewerEntry bind:segmentationData={segmentation} on:delete={showDeleteModal}/>
                    {/if}
                {/each}
                {#if noSegmentationsToShow()}
                    <p class="no-segmentations-hint">Keine fertigen Segmentierungen vorhanden.</p>
                {/if}
            </Card>
        </div>
        <PapayaViewer/>
    </div>
    <Modal bind:showModal on:cancel={() => {}} on:confirm={() => deleteClicked()} cancelButtonText = "Abbrechen" cancelButtonClass = "main-button" 
        confirmButtonText = "Löschen" confirmButtonClass = "error-button">
        <h2 slot="header">
            Segmentierung löschen?
        </h2>
        <p>
            Soll die Segmentierung <i>{segmentationToDelete.segmentationName}</i> gelöscht werden? Dies kann nicht rückgängig gemacht werden!
        </p>
    </Modal>
</PageWrapper>

<style>
    .container {
        display: flex;
        flex-direction: row;
        justify-content: left;
    }
    .side-card {
        display: flex;
        min-width: 500px;
    }
    .no-segmentations-hint {
        /* margin-top: 20px; */
    }
</style>