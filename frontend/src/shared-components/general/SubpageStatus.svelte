<script>

    import Card from "./Card.svelte"
    import ArrowRightLongSymbol from "../svg/ArrowRightLongSymbol.svelte"
    import { createEventDispatcher } from "svelte"
        
    const dispatch = createEventDispatcher()

    export let statusList

    // This function is called when the user has clicked on one of the SubpageStatus elements and wants to 
    // go back to one of the previous states in the list. This is taken care of by the parent component.
    function statusChanged(index) {
        dispatch("statusChanged", index)
    }

</script>


<div class="container">
    <div class="sub-container">
        <Card dropShadow={false} secondaryBackground={true} narrowPadding={true}>
            <div class="card-content">
                {#each statusList as statusElement, index}
                    <!-- If the element is not the last element in the list, show an arrow after the current element, else only show the element itself. -->
                    {#if (index !== statusList.length - 1)}
                        <div class="status-element" on:click={() => statusChanged(index)}>{statusElement.name}</div>
                        <div class="arrow-container">
                            <ArrowRightLongSymbol/>
                        </div>
                    {:else}
                        <div class="status-element last-element" on:click={() => statusChanged(index)}>{statusElement.name}</div>
                    {/if}
                {/each}
            </div>
        </Card>
    </div>
</div>


<style>
.container {
    margin-bottom: 35px;
    display: flex;
    justify-content: center;
    align-items: center;
}
.card-content {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
}
.status-element {
    padding: 6px;
    cursor: pointer;
    transition: all .5s ease;
}
.status-element:hover {
    color: white;
}
.arrow-container {
    margin-top: 6px;
}
</style>