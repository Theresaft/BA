<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import PapayaViewer from "../../single-components/PapayaViewer.svelte";
    import Card from "../../shared-components/Card.svelte";
    import SearchBar from "../../shared-components/SearchBar.svelte";

    let prompt = ""

    $: {
        console.log(prompt)
    }

</script>

<PageWrapper removeMainSideMargin={true}>
    <div class="container">
        <div class="side-card">
            <Card title="Letzte Segmentierungen" center={true} dropShadow={false} borderRadius={false}>
                <SearchBar bind:prompt={prompt}>

                </SearchBar>
            </Card>
        </div>
        <PapayaViewer/>
    </div>
</PageWrapper>

<style>
    .container {
        display: flex;
        flex-direction: row;
        justify-content: left;
    }
    .side-card {
        display: flex;
    }
</style>