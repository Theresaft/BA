<script>
    import { 
        Enums as csToolsEnums,
        segmentation,
    } from '@cornerstonejs/tools';
    import {viewerState, segmentationLoaded} from "../../stores/ViewerStore"


    export let classLabel; // e.g. { name: 'Necrotic Core', opacity: 50, isVisible: true, segmentIndex: 1 },

    let labelColor = "rgba(168, 168, 168, 1)"; // Default color (gray)


    $: {
        // Currently segmentationLoaded is written to the store once everything is done
        if ($segmentationLoaded) {
            getLabelColor()
        }
    }


    function handleSliderChange(event) {

        // Save opacity in label state
        classLabel.opacity = event.target.value;
        
        const segmentFillAlpha = Number(classLabel.opacity) / 100;

        // Set new alpha value for the segments fill color
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

    // https://github.com/cornerstonejs/cornerstone3D/issues/1862
    // https://github.com/cornerstonejs/cornerstone3D/issues/1841
    function handleCheckboxChange(event){
        for(const viewportID of $viewerState.viewportIds){
            segmentation.config.visibility.setSegmentIndexVisibility(
                viewportID,
                {
                    segmentationId: $viewerState.segmentationId,
                    type : csToolsEnums.SegmentationRepresentations.Labelmap
                },
                classLabel.segmentIndex,
                classLabel.isVisible
            );

        }
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
    <div class="label-top-container">
        <div class="label-color" style="background-color: {labelColor}"></div>
        <div class="label-name">
            {classLabel.name}
        </div>
        <label class="label-switch">
            <input type="checkbox" bind:checked={classLabel.isVisible} on:change={handleCheckboxChange}>
            <span class="slider round"></span>
        </label>
    </div>
    <input type="range" min="0" max="100" bind:value={classLabel.opacity} on:input={handleSliderChange}>
</div>


<style>
.label-container{
    display: flex;
    flex-direction: column;
    background-color:black;
    padding: 5px;
    border: 1px solid rgb(255, 255, 255);
    border-radius: 4px;
    padding: 5px 10px;
}
.label-top-container{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}
.label-color{
    width: 20px;
    height: 20px;
    border-radius: 3px;
}
.label-name{
    white-space: nowrap;
}

.label-switch {
    position: relative;
    display: inline-block;
    width: 30px;
    height: 18px;
}

.label-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .1s;
    border-radius: 20px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 12px;
    width: 12px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .1s;
    border-radius: 50%;
}

input:checked + .slider {
    background-color: var(--button-color-preview);
}

input:checked + .slider:before {
    transform: translateX(12px);
}


</style>