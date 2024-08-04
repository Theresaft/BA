<script>
    import { createEventDispatcher, onMount } from "svelte"
    
    const dispatch = createEventDispatcher()
    export let title = ""
    export let center = false
    export let dropShadow = true
    export let className = ""
</script>

<div class="card {className}" class:drop-shadow={dropShadow}>
    <!-- Only reserve space for the title if the title is non-empty. -->
     <div class="header-wrapper">
        <div class="slot-wrapper" on:click={() => dispatch("symbolClick", {})}>
            <slot name="symbol" class="symbol"/>
        </div>
        <h2 class="title" class:hide={title === ""} class:center={center}>{title}</h2>
    </div>
    <slot></slot>
</div>

<style>
    .header-wrapper {
        display: flex;
        flex-direction: row;
        justify-content: center;
    }
    .slot-wrapper {
        margin-right: auto;
        cursor: pointer;
    }
    .title {
        margin: 0;
        padding: 0;
        margin-bottom: 20px;
        font-size: 26px;
        margin-right: auto;
    }
    .card {
        background-color: var(--background-color-card);
        border-radius: 7px;
        padding: 20px 25px 25px 25px;
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