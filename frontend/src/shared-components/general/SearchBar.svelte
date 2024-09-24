<script>
    import SearchSymbol from "../svg/SearchSymbol.svg"
    import CrossSymbol from "../svg/CrossSymbol.svelte"
    import { createEventDispatcher, getContext } from "svelte"
    const dispatch = createEventDispatcher()

    export let prompt = ""

    $: {
        dispatch("promptChanged", prompt)
    }
</script>

<div class="container">
    <!-- <SearchSymbol/> -->
    <input type="text" class="input" placeholder="Segmentierung suchen" bind:value={prompt}>
    <button class="cross-symbol-button error-button button" on:click={() => {prompt = ""}}>
        <CrossSymbol/>
    </button>
</div>

<style>
    .container {
        padding: 10px 10px;
        margin-bottom: 20px;
        display: flex;
    }
    .input {
        border-radius: 5px;
        font-size: 15px;
        background: url("../svg/SearchSymbol.svg") no-repeat scroll 7px 10px;
        background-color: aliceblue;
        width: 100%;
        padding-left: 25px;
    }
    .cross-symbol-button {
        cursor: pointer;
        display: block;
        border-radius: 7px;
        padding: 7px 9px;
        margin-bottom: auto;
        margin-left: 10px;
    }
</style>