<script>
    export let prompt = ""

    $: {
        console.log(prompt)
    }
</script>

<div class="container">
    <input type="text" class="input" bind:value={prompt}>
</div>

<style>
    .input {
        border-radius: 5px;
        font-size: 20px;
    }
</style>