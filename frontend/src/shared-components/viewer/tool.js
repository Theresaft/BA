/**
 * This file contains all helper functions for cornerstone tools
 */

import { get } from "svelte/store";

// Cornerstone TOOLS
import {
    Enums as csToolsEnums,
    CrosshairsTool,
} from '@cornerstonejs/tools';
const { MouseBindings } = csToolsEnums;


import { viewerState} from "../../stores/ViewerStore"


// Crosshair helper functions
export function getReferenceLineColor(viewportId) {

    const currentViewerState = get(viewerState)

    const viewportColors = {
        [currentViewerState.viewportIds[0]]: 'rgb(200, 0, 0)',
        [currentViewerState.viewportIds[1]]: 'rgb(200, 200, 0)',
        [currentViewerState.viewportIds[2]]: 'rgb(0, 200, 0)',
    };

    return viewportColors[viewportId];
}

export function getReferenceLineControllable(viewportId) {
    const currentViewerState = get(viewerState)

    const index = currentViewerState.viewportIds.indexOf(viewportId);
    return index !== -1;
}

export function getReferenceLineDraggableRotatable(viewportId) {
    const currentViewerState = get(viewerState)

    const index = currentViewerState.viewportIds.indexOf(viewportId);
    return index !== -1;
}

export function getReferenceLineSlabThicknessControlsOn(viewportId) {
    const currentViewerState = get(viewerState)

    const index = currentViewerState.viewportIds.indexOf(viewportId);
    return index !== -1;
}

    
export function toogleBrush(){
    const currentToolState = get(toolState)
    const currentViewerState = get(viewerState)


    if(currentToolState.brushIsActive){
        currentViewerState.toolGroup.setToolPassive("CircularBrush");
        currentViewerState.toolGroup.setToolActive(CrosshairsTool.toolName, {
            bindings: [{ mouseButton: MouseBindings.Primary }],
        });
    } else {
        currentViewerState.toolGroup.setToolPassive(CrosshairsTool.toolName);
        currentViewerState.toolGroup.setToolActive("CircularBrush", {
        bindings: [
            {
                mouseButton: MouseBindings.Primary, // Left Click
            },
        ],
        });
    }

    toolState.update(state => {
        return { ...state, brushIsActive: !state.brushIsActive };
    });

}
