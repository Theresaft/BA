/**
 * This file contains all helper functions for creating a segmentation object in cornerstone
*/

// Svelte 
import { get } from "svelte/store";
// Cornerstone CORE
import {
    volumeLoader,
} from '@cornerstonejs/core';
// Cornerstone TOOLS
import { 
    Enums as csToolsEnums,
    segmentation,
} from '@cornerstonejs/tools';
import { v4 as uuidv4 } from 'uuid';

import {viewerState, images} from "../../stores/ViewerStore"

  
  
  // ================================================================================
  // ========================= Create Empty Segmentation ============================
  // ================================================================================
  
  export async function addActiveSegmentation() {

    const currentViewerState = get(viewerState)

    if (!currentViewerState.volumeId) {
        console.error("Segmentation can't be loaded before base images are loaded");
        return;
    }

    // Generate segmentation id
    const segmentationId = uuidv4()

    // Add some segmentations based on the source data stack
    await addSegmentationsToState(segmentationId);

  }

  async function addSegmentationsToState(segmentationId) {
    // Create a segmentation of the same resolution as the source data

    const currentViewerState = get(viewerState)
    const currentImageState = get(images)

    const derivedVolume =
        await volumeLoader.createAndCacheDerivedLabelmapVolume(currentViewerState.volumeId, {
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
    for (let i = 0; i < length; i++) {
        const segmentationValue = flatSegmentationArray[i] || 0; 

        if (segmentationValue > 0) { 
            // TODO: Remember which classLabel corresponds to which segmentIndex
            voxelManager.setAtIndex(i, segmentationValue); 
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

    // Save segmentationId in store once everything is done
    viewerState.update(state => ({
        ...state,
        segmentationId: segmentationId
    }));

    return derivedVolume;
  }


  export async function removeSegmentation(segmentationID){
    segmentation.removeSegmentation(segmentationID)
  }