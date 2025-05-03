/**
 * This file contains all helper functions for creating a segmentation object in cornerstone
*/

// Svelte 
import { get } from "svelte/store";
// Cornerstone CORE
import {
    volumeLoader,
    cache
} from '@cornerstonejs/core';
// Cornerstone TOOLS
import { 
    Enums as csToolsEnums,
    segmentation,
} from '@cornerstonejs/tools';
import { v4 as uuidv4 } from 'uuid';

import {viewerState, images, labelState} from "../../stores/ViewerStore"

  
  
// ================================================================================
// ========================= Create Empty Segmentation ============================
// ================================================================================

export async function addActiveSegmentation() {

    const currentViewerState = get(viewerState)

    if (!currentViewerState.imageVolumeID) {
        console.error("Segmentation can't be loaded before base images are loaded");
        return;
    }

    // Set cornerstones segmentation id based on our segmentation id
    const segmentationId = get(viewerState).segmentationId

    // Add some segmentations based on the source data stack
    await addSegmentationsToState(segmentationId);

}

async function addSegmentationsToState(segmentationId) {
    // Create a segmentation of the same resolution as the source data

    const currentViewerState = get(viewerState)
    const currentImageState = get(images)

    // This will throw an error when the derived segemention volume is already in the cache (we didn't find a way to check the cache)  
    if(!cache.getVolume(segmentationId)){
        const derivedVolume = await volumeLoader.createAndCacheDerivedLabelmapVolume(currentViewerState.imageVolumeID, {
            volumeId: segmentationId
        });


        // Get segmentation data
        const segmentationArray = currentImageState.labels; 


        if (!segmentationArray || segmentationArray.length === 0) {
            console.error("Invalid segmentation data received");
            return;
        }


        const voxelManager = derivedVolume.voxelManager;
        const length = voxelManager.getScalarDataLength();
        const flatSegmentationArray = segmentationArray.flat(Infinity); 


        // Set pixels based on segmentation values
        // This is how the labels are set by the models: { "background": 0, "edema": 1, "non_enhancing_and_necrosis": 2, "enhancing_tumor": 3 }
        // Since cornerstone doesn't allow explicitly setting the segment indicies we have this workaround of adding each class after another    
        for(const label of [1,2,3]){
            for (let i = 0; i < length; i++) {
                const segmentationValue = flatSegmentationArray[i] || 0; 
                if (segmentationValue == label) { 
                    voxelManager.setAtIndex(i, segmentationValue); 
                }
            }
        }

    } 

    // Add the segmentations to state
    segmentation.addSegmentations([
        {
            segmentationId,
            representation: {
                // The type of segmentation
                type: csToolsEnums.SegmentationRepresentations.Labelmap,
                // The actual segmentation data, in the case of labelmap this is a
                // reference to the source volume of the segmentation.
                data: {
                    volumeId: segmentationId
                }
            },
            config: {
                segments: {
                    1: {
                        active: false
                    },
                    2 : {
                        active: false
                    },
                    3 : {
                        active: false
                    }
                },
            }
        }
    ]);

    const segmentationRepresentation = {
        segmentationId,
    };

    await segmentation.addLabelmapRepresentationToViewportMap({
        [currentViewerState.viewportIds[0]]: [segmentationRepresentation],
        [currentViewerState.viewportIds[1]]: [segmentationRepresentation],
        [currentViewerState.viewportIds[2]]: [segmentationRepresentation],
    });

    return ;
}


// Removes segementation completely
export async function removeSegmentation(segmentationID){
    segmentation.removeSegmentation(segmentationID)
}


// Remove segmentation representations from viewports (Note: Segmentation is not removed completely)
export async function removeAllSegmentationRepresentations(){
    segmentation.removeAllSegmentationRepresentations();
}

// Adds segmentation representation to the viewports
export async function addSegmentationRepresentations(){

    const currentViewerState = get(viewerState)
    const currentLabelState = get(labelState)

    const segmentationId = currentViewerState.segmentationId
    const segmentationRepresentation = {
        segmentationId,
    };

    // Add Segmentation representation
    await segmentation.addLabelmapRepresentationToViewportMap({
        [currentViewerState.viewportIds[0]]: [segmentationRepresentation],
        [currentViewerState.viewportIds[1]]: [segmentationRepresentation],
        [currentViewerState.viewportIds[2]]: [segmentationRepresentation],
    });

    // Set the visibilty of the segmentation representation according to the state
    setSegmentVisibilityBasedOnStore(segmentationId)

}

export async function setSegmentVisibilityBasedOnStore(segmentationId, updateCamera = true){    
    const currentViewerState = get(viewerState)
    const currentLabelState = get(labelState)

    for(const [index, viewportID] of currentViewerState.viewportIds.entries()){
        for(const label of currentLabelState){
            
            segmentation.config.visibility.setSegmentIndexVisibility(
                viewportID,
                {
                    segmentationId: segmentationId,
                    type : csToolsEnums.SegmentationRepresentations.Labelmap
                },
                label.segmentIndex,
                label.isVisible
            );
        }

        // This is a dirty workaround
        // The problem is that setSegmentIndexVisibility and addLabelmapRepresentationToViewportMap seem to reset the camera
        // Thus we need to set the correct camera position afterwards.
        if(updateCamera){
            setTimeout(async () => {
                const viewport = currentViewerState.renderingEngine.getViewport(viewportID)
                await viewport.setCamera(currentViewerState.cameras[index], false);
                await viewport.render();
            }, 1);
        }
    }
}


export function resetSegmentationStyles(){
    segmentation.config.style.resetToGlobalStyle()

    const currentViewerState = get(viewerState)
    const segmentationId = currentViewerState.segmentationId
    setSegmentVisibilityBasedOnStore(segmentationId, false)
}