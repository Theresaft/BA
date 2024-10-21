<script>
    export let segmentation = {}
</script>


<div class="segmentations-view">
    <div class="segmentation-title">{segmentation.segmentationName}</div>

    <div class="sequences-overview">
        <div class="t1-wrapper">
            <div>T1</div>
            <div>{segmentation.sequenceMappings.find(obj => obj.t1).t1}</div>
        </div>
        <div class="t1-km-wrapper">
            <div>T1-KM</div>
            <div>{segmentation.sequenceMappings.find(obj => obj.t1KM).t1KM}</div>
        </div>
        <div class="t2-wrapper">
            <div>T2</div>
            <div>{segmentation.sequenceMappings.find(obj => obj.t2).t2}</div>
        </div>
        <div class="flair-wrapper">
            <div>Flair</div>
            <div>{segmentation.sequenceMappings.find(obj => obj.flair).flair}</div>
        </div>
    </div>

    <div class="model-wrapper">
        <div>Modell:</div>
        <div>{segmentation.model}</div>
    </div>
    <div class="date-wrapper">
        <div>Datum:</div>
        <div>{segmentation.date}</div>
    </div>
    <!-- <button class="trash-button" on:click={() => dispatch("delete", segmentationData)}><TrashSymbol/></button> -->
</div>

<style>

</style>