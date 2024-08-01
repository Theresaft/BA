<script>
    import {AvailableModels} from "../stores/Store.js"
</script>

<div class="model-select-wrapper">
    <h3 class="description"> KI-Modell für die Segmentierung: </h3>
    <select name="model-select" id="model-select" class="model-select">
        {#each AvailableModels as model}
            <option value={model.id}>{model.displayName}</option>
        {/each}
    </select>
</div>

<style>
    .model-select-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .description {
        text-align: center;
    }
    .model-select {
        -webkit-appearance: menulist-button;
        height: 40px;
        font-size: 14px;
    }
</style>