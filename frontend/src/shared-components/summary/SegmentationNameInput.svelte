<script>
    export let segmentationTitle
    export let segmentationTitleError
</script>

<div class="container">
    <h3 class="description">Name für die Segmentierung:</h3>
    <input type="text" placeholder="Name für Segmentierung" class="segmentation-input" bind:value={segmentationTitle}>
    <p class="error-text">{segmentationTitleError}</p>
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
    .error-text {
        font-size: 15px;
        color: var(--button-color-error);
        /* text-shadow: white 0 0 3px; */
        width: 40%;
        padding: 6px 0;
        text-align: center;
        font-weight: 600;
    }
</style>