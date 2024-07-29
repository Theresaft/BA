<script>
    export let title = ""
    export let center = false
    export let dropShadow = true
</script>

<div class="card" class:drop-shadow={dropShadow}>
    <!-- Only reserve space for the title if the title is non-empty. -->
    <h2 class="title" class:hide={title === ""} class:center={center}>{title}</h2>
    <slot></slot>
</div>

<style>
    .title {
        margin: 0;
        padding: 0;
        margin-bottom: 20px;
        font-size: 22px;
    }
    .card {
        background-color: var(--background-color-card);
        border-radius: 7px;
        padding: 25px;
    }
    .drop-shadow {
        box-shadow: 3px 3px 3px rgba(220, 220, 255, 75%);
    }
    .center {
        text-align: center;
    }
    .hide {
        display: none;
    }
</style>