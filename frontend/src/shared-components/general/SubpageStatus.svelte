<script>

import Card from "./Card.svelte";
import ArrowRightLongSymbol from "../svg/ArrowRightLongSymbol.svelte";

// This is the list of subpages that the user has navigated to. The list will be shown in the form of "Element 1" => "Element 2" => ...
export let statusList = ["Home", "My Project", "Summary"]

</script>


<div class="container">
    <div class="sub-container">
        <Card dropShadow={false} secondaryBackground={true}>
            <div class="card-content">
                {#each statusList as statusElement, index}
                    <!-- If the element is not the last element in the list, show an arrow after the current element, else only show the element itself. -->
                    {#if (index !== statusList.length - 1)}
                        <div class="status-element">{statusElement}</div>
                        <div class="arrow-container">
                            <ArrowRightLongSymbol/>
                        </div>
                    {:else}
                        <div class="status-element last-element">{statusElement}</div>
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
}
.status-element {
}
.arrow-container {
    margin-top: 6px;
}
</style>