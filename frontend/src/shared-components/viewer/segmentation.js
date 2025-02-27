/**
 * This file contains all helper functions for creating a segmentation object in cornerstone
*/

// Svelte 
import {rawSegmentationDataAPI} from "../../lib/api"
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

import {viewerState} from "../../stores/ViewerStore"

  
  
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

    const derivedVolume =
        await volumeLoader.createAndCacheDerivedLabelmapVolume(currentViewerState.volumeId, {
            volumeId: segmentationId
        });


    // Fetch segmentation data
    const response = await rawSegmentationDataAPI(segmentationId);

    // Extract the segmentation array from the response
    const segmentationArray = response.segmentation; // Assuming it's a 3D array

    
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
        
        voxelManager.setAtIndex(i, segmentationValue); 
        // TODO: Remember which classLabel corresponds to which segmentIndex
        // voxelManager.setAtIndex(i, 100); 
      }
    }

    
    // const voxelManager = derivedVolume.voxelManager;
    // const length = voxelManager.getScalarDataLength();
    // for (let i = 0; i < length; i++) {
      
    //   // if () {
    //   if(i % 2 == 0){
    //     voxelManager.setAtIndex(i, 200);
    //   }
      
    //   // }
    // }

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
            }
        }
    ]);

    // Set global segmentation styles
    segmentation.config.style.setStyle(
        { 
            type: csToolsEnums.SegmentationRepresentations.Labelmap
         },
        { 
            renderOutline: false,
            // outlineWidth: 0
            fillAlpha: 1 // Initial fill value for all segmentations
        }
      );
      

    // Add the segmentation representation to the viewport
    await segmentation.addSegmentationRepresentations(currentViewerState.viewportIds[0], [
        {
            segmentationId,
            type: csToolsEnums.SegmentationRepresentations.Labelmap
        }
    ]);

    await segmentation.addSegmentationRepresentations(currentViewerState.viewportIds[1], [
        {
            segmentationId,
            type: csToolsEnums.SegmentationRepresentations.Labelmap
        }
    ]);

    await segmentation.addSegmentationRepresentations(currentViewerState.viewportIds[2], [
        {
            segmentationId,
            type: csToolsEnums.SegmentationRepresentations.Labelmap
        }
    ]);

    // Save segmentationId in store once everything is done
    viewerState.update(state => ({
        ...state,
        segmentationId: segmentationId
    }));

    return derivedVolume;
  }

