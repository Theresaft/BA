<script>
    import SearchSymbol from "../svg/SearchSymbol.svg";
    import CrossSymbol from "../svg/CrossSymbol.svelte"

    export let prompt = ""

    $: {
        console.log(prompt)
    }
</script>

<div class="container">
    <!-- <SearchSymbol/> -->
    <input type="text" class="input" placeholder="Segmentierung suchen" bind:value={prompt}>
    <button class="cross-symbol-button" on:click={() => {prompt = ""}}>
        <CrossSymbol></CrossSymbol>
    </button>
</div>

<style>
    .container {
        padding: 10px 10px;
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
        all: unset;
        cursor: pointer;
        display: block;
        background-color: var(--button-color-main);
        border-radius: 7px;
        padding: 7px 9px;
        margin-bottom: auto;
        margin-left: 10px;
    }
</style>