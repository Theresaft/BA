<script>
    export let segmentationTitle = ""
</script>

<div class="container">
    <h3 class="description">Wählen Sie einen Namen für die Segmentierung:</h3>
    <input type="text" placeholder="Name für Segmentierung" class="segmentation-input" bind:value={segmentationTitle}>
</div>

<style>
    .container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 68.72px;
    }
    .description {
        width: 60%;
        text-align: center;
    }
    .segmentation-input {
        width: 40%;
        text-align: left;
        margin-top: 15px;
        font-size: 14px;
        padding: 6px 10px;
        border-radius: 2px;
    }
</style>