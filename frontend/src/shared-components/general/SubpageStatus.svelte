<script>

import Card from "./Card.svelte"
import ArrowRightLongSymbol from "../svg/ArrowRightLongSymbol.svelte"
import PageStatus from "../../routes/segmentation/+page.svelte"

export let statusList

$: {
    console.log(statusList)
}

</script>


<div class="container">
    <div class="sub-container">
        <Card dropShadow={false} secondaryBackground={true} narrowPadding={true}>
            <div class="card-content">
                {#each statusList as statusElement, index}
                    <!-- If the element is not the last element in the list, show an arrow after the current element, else only show the element itself. -->
                    {#if (index !== statusList.length - 1)}
                        <div class="status-element">{statusElement.name}</div>
                        <div class="arrow-container">
                            <ArrowRightLongSymbol/>
                        </div>
                    {:else}
                        <div class="status-element last-element">{statusElement.name}</div>
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
.arrow-container {
    margin-top: 6px;
}
</style>