<script>
    import { 
        Enums as csToolsEnums,
        segmentation,
    } from '@cornerstonejs/tools';
    import {viewerState} from "../../stores/ViewerStore"


    export let classLabel; 

    let sliderValue = 100; // Default value
    let labelColor = "rgba(168, 168, 168, 1)"; // Default color (gray)


    $: {
        // Currently segmentationId is written to the store once everything is done
        if ($viewerState.segmentationId) {
            getLabelColor()
        }
    }


    function handleSliderChange(event) {
        sliderValue = event.target.value;
        
        const segmentFillAlpha = Number(sliderValue) / 100;

        segmentation.config.style.setStyle(
            {
                segmentationId: $viewerState.segmentationId,
                type: csToolsEnums.SegmentationRepresentations.Labelmap,
                segmentIndex: classLabel.segmentIndex,
            },
            {
                fillAlpha: segmentFillAlpha,
            }
        );

    }

    function getLabelColor(){
        const color = segmentation.config.color.getSegmentIndexColor(
            $viewerState.viewportIds[0],
            $viewerState.segmentationId,
            classLabel.segmentIndex
        );
        
        // Convert [R, G, B, A] to "rgba(R, G, B, A)"
        labelColor = `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${color[3] / 255})`;
    }


</script>

<div class="label-container">
    <div class="label-text">
        <div class="label-color" style="background-color: {labelColor}"></div>
        <div class="label-name">
            {classLabel.labelName}
        </div>
    </div>
    <input type="range" min="0" max="100" bind:value={sliderValue} on:input={handleSliderChange}>
</div>


<style>
.label-container{
    display: flex;
    flex-direction: column;
    background-color:black;
    padding: 5px;
    border: 1px solid rgb(255, 255, 255);
    width: 170px; /**Static label container size could possibly be removed*/
    border-radius: 4px;}
.label-text{
    display: flex;
    align-items: center;
}
.label-color{
    width: 20px;
    height: 20px;
    border-radius: 3px;
    margin: 0px 10px;
}
.label-name{
    white-space: nowrap;
}


</style>