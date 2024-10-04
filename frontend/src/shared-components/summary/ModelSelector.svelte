<script>
    import {AvailableModels} from "../../stores/Store.js"

    export let selectedModel

</script>

<div class="model-select-wrapper">
    <h3 class="title"> KI-Modell für die Segmentierung: </h3>
    <select name="model-select" id="model-select" class="model-select" bind:value={selectedModel}>
        {#each AvailableModels as model}
            <option value={model.id}>{model.displayName}</option>
        {/each}
    </select>
    <p class="description">
        {#each AvailableModels as model}
            {#if model.id === selectedModel}
                {model.description}
            {/if}
        {/each}
    </p>
</div>

<style>
    .model-select-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 50px;
    }
    .title {
        text-align: center;
    }
    .model-select {
        -webkit-appearance: menulist-button;
        height: 40px;
        font-size: 14px;
        text-align: center;
        margin-top: 15px;
    }
    .description {
        margin-bottom: 0;
    }
</style>