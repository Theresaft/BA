/**
 * This file contains all helper functions for cornerstone tools of the preview viewer
 */

import { get } from "svelte/store";
import { previewViewerState} from "../../stores/ViewerStore"

// Crosshair helper functions
export function getReferenceLineColor(viewportId) {

    const currentViewerState = get(previewViewerState)

    const viewportColors = {
        [currentViewerState.viewportIds[0]]: 'rgb(200, 0, 0)',
        [currentViewerState.viewportIds[1]]: 'rgb(200, 200, 0)',
        [currentViewerState.viewportIds[2]]: 'rgb(0, 200, 0)',
    };

    return viewportColors[viewportId];
}

export function getReferenceLineControllable(viewportId) {
    const currentViewerState = get(previewViewerState)

    const index = currentViewerState.viewportIds.indexOf(viewportId);
    return index !== -1;
}

export function getReferenceLineDraggableRotatable(viewportId) {
    const currentViewerState = get(previewViewerState)

    const index = currentViewerState.viewportIds.indexOf(viewportId);
    return index !== -1;
}

export function getReferenceLineSlabThicknessControlsOn(viewportId) {
    const currentViewerState = get(previewViewerState)

    const index = currentViewerState.viewportIds.indexOf(viewportId);
    return index !== -1;
}

