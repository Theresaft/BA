/**
 * This file contains all helper functions for loading dicom or nifti images as a cornerstone volume
*/

import { get } from "svelte/store";

// Cornerstone CORE
import {
    volumeLoader,
    setVolumesForViewports,
    imageLoader,
    getRenderingEngine,
    cache
} from '@cornerstonejs/core';

// Dicom Image Loader
import cornerstoneDICOMImageLoader from '@cornerstonejs/dicom-image-loader';

// dicom client
import { v4 as uuidv4 } from 'uuid';

import {
  cornerstoneNiftiImageLoader,
  createNiftiImageIdsAndCacheMetadata,
} from '@cornerstonejs/nifti-volume-loader';



import {images, viewerState, previewViewerState, viewerIsLoading, segmentationLoaded, previewViewerAlreadySetup, previewImage, previewViewerIsLoading} from "../../stores/ViewerStore"
import {addActiveSegmentation, addSegmentationRepresentations, removeAllSegmentationRepresentations } from "./segmentation"


// Loads image volume from cache or creates new ones
async function loadAndCacheImages(){
  const segmentationId = get(viewerState).segmentationId;
  const volumeLoaderScheme = 'cornerstoneStreamingImageVolume'; // Loader id which defines which volume loader to use
  for(const modality of ["t1","t1km","t2","flair"]){

    const volumeID = `${volumeLoaderScheme}:${segmentationId}` + modality; 
    let volume = cache.getVolume(volumeID);
  
    if (!volume) {
      console.log("Creating New Volume");
  
      let imageIds = []
  
      // Load images using cornerstones loader
      const current_images = get(images)
      for (let i = 0; i < current_images[modality].length; i++) {
          const imageSlice = current_images[modality]
          const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(imageSlice[i]);
          imageIds.push(imageId);
      }
      await prefetchMetadataInformation(imageIds);
    
  
      // Define a volume in memory, when it existed
      if (imageIds.length !== 0) {
          volume = await volumeLoader.createAndCacheVolume(volumeID, {
        imageIds,
      });

      // Set the volume to load
      volume.load();
      }
    }

  }
} 

export async function loadImages(modality){
  const currentViewerState = get(viewerState);
  const axialViewportID = currentViewerState.viewportIds[0] 
  const sagitalViewportID = currentViewerState.viewportIds[1]
  const coronalViewportID = currentViewerState.viewportIds[2] 

  const segmentationId = get(viewerState).segmentationId;
  const volumeLoaderScheme = 'cornerstoneStreamingImageVolume'; // Loader id which defines which volume loader to use
  const volumeID = `${volumeLoaderScheme}:${segmentationId}` + modality; 

  // Update viewerstate
  viewerState.update((state) => ({
      ...state,
      imageVolumeID: volumeID,
      currentlyDisplayedModality: modality,
  }));  

  await loadAndCacheImages()
  
  // Note: Timeout is need because loading from cache is not fully complete otherwise
  setTimeout(async () => {

    // Set volumes to viewport
    await setVolumesForViewports(
      get(viewerState).renderingEngine,
      [{ volumeId: get(viewerState).imageVolumeID }],
      [axialViewportID, sagitalViewportID, coronalViewportID]
    );

    // Configure Viewport properties
    for(const [index, viewportID] of get(viewerState).viewportIds.entries()){
      const viewport = get(viewerState).renderingEngine.getViewport(viewportID)
      
      // Set window leveling
      const voiRange = { lower: get(viewerState).currentWindowLeveling[modality].min, upper: get(viewerState).currentWindowLeveling[modality].max };
      
      await viewport.setProperties({ voiRange: voiRange });
  
      // Set colormap
      viewport.setProperties({ colormap: { name:  get(viewerState).colormap} });
  
      // Note: Don't use viewport.setCamera() and viewport.render() here, since it will be triggered internally when adding the segmentation
  
    }

    // Load segmentation when it is first loaded. Otherwise only readd segmentation representation (e.g. on page change)
    // Note: This will also trigger the camera update
    if(!get(segmentationLoaded)){
      addActiveSegmentation();
      segmentationLoaded.set(true)
    } else {
      removeAllSegmentationRepresentations()
      addSegmentationRepresentations()
    }

    viewerIsLoading.set(false)  

  }, 1);

}
// Returns true if all modality volumes and segmentation volume is cached already
export function imagesAndSegmentationInCache(segmentationId){
  // check segmentation volume in cache
  if(!cache.getVolume(segmentationId)){    
    return false
  }

  // check if image volumes are in cache for every modality
  for(const modality of ["t1","t1km","t2","flair"]){
    const volumeLoaderScheme = 'cornerstoneStreamingImageVolume'; // Loader id which defines which volume loader to use
    const volumeID = `${volumeLoaderScheme}:${segmentationId}` + modality; 
    
    if(!cache.getVolume(volumeID)){
      return false
    }
  }

  return true

}


export async function loadPreviewImage(){
  const currentViewerState = get(previewViewerState)
  const axialViewportID = currentViewerState.viewportIds[0]
  const sagitalViewportID = currentViewerState.viewportIds[1]
  const coronalViewportID = currentViewerState.viewportIds[2]
  
  let imageIds = []

  const image = get(previewImage)
  
  for (let i = 0; i < image.length; i++) {
    const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(image[i]);
    imageIds.push(imageId);
  }

  await prefetchMetadataInformation(imageIds);

  // Define a volume in memory
  const volumeID = uuidv4();
  const volume = await volumeLoader.createAndCacheVolume(volumeID, {
    imageIds,
  });

  volume.load();

  while(!get(previewViewerAlreadySetup)){}

  await setVolumesForViewports(
    currentViewerState.renderingEngine,
    [{ volumeId: volumeID }],
    [axialViewportID, sagitalViewportID, coronalViewportID]
  );

  for(const viewportID of [axialViewportID, sagitalViewportID, coronalViewportID]){
    const viewport = currentViewerState.renderingEngine.getViewport(viewportID)

    // Render the image
    await viewport.render();
  }

  previewViewerIsLoading.set(false)
}


// preloads imageIds metadata in memory
async function prefetchMetadataInformation(imageIdsToPrefetch) {
  for (let i = 0; i < imageIdsToPrefetch.length; i++) {
    await cornerstoneDICOMImageLoader.wadouri.loadImage(imageIdsToPrefetch[i]).promise;
  }
}



// ================================================================================
// ============================= Load Nifti Images ================================
// ================================================================================



export async function loadNiftiImage(){
    const currentViewerState = get(viewerState);
    const axialViewportID = currentViewerState.viewportIds[0] 
    const sagitalViewportID = currentViewerState.viewportIds[1]
    const coronalViewportID = currentViewerState.viewportIds[2]

  
    // const blobURL = await getNifti() 
    // const niftiURL = blobURL
    
    // const niftiURL = 'https://ohif-assets.s3.us-east-2.amazonaws.com/nifti/CTACardio.nii.gz';
    const niftiURL = "http://127.0.0.1:5001/brainns-api/images/preprocessed/nifti/test-nifti.nii.gz" 

    imageLoader.registerImageLoader('nifti', cornerstoneNiftiImageLoader);
    const imageIds = await createNiftiImageIdsAndCacheMetadata({
        url: niftiURL 
    });


    viewerState.update(state => ({
        ...state,
        referenceImageIds: imageIds
    }));

    const volumeID = uuidv4();

    viewerState.update(state => ({
        ...state,
        imageVolumeID: volumeID
    }));    
 
    // Define a volume in memory
    volume = await volumeLoader.createAndCacheVolume(volumeID, {
        imageIds,
    });
  
    volume.load();


    // Set the camera
    // setCamera(rowVec, colVec, axialViewportID, sagitalViewportID, coronalViewportID)



    setVolumesForViewports(
        currentViewerState.renderingEngine,
      [{ volumeId: volumeID }],
      [axialViewportID, sagitalViewportID, coronalViewportID]
    );


}


// TODO: Figure out how to change the camera orientations of the viewports dynamically
function setCamera(rowVec, colVec, axialViewportID, sagitalViewportID, coronalViewportID){

    // const viewport0 = getEnabledElementByViewportId(axialViewportID)
    // const viewport1 = getEnabledElementByViewportId(sagitalViewportID)
    // const viewport2 = getEnabledElementByViewportId(coronalViewportID)
    const renderingEngine = getRenderingEngine("MY_RENDERING_ENGINE_ID");

    // Get the volume viewport
    const viewport0 = renderingEngine.getViewport(axialViewportID)
    const viewport1 = renderingEngine.getViewport(sagitalViewportID)
    const viewport2 = renderingEngine.getViewport(coronalViewportID)
    

    // Compute slice normal (cross product of row and column vectors)
    const sliceNormalVec = [
        rowVec[1] * colVec[2] - rowVec[2] * colVec[1],
        rowVec[2] * colVec[0] - rowVec[0] * colVec[2],
        rowVec[0] * colVec[1] - rowVec[1] * colVec[0],
    ];

    // Axial View (Top-down)
    const axialViewPlaneNormal = colVec
    const axialViewUp = rowVec.map((val) => -val); 

    // Sagittal View (Side View)
    const sagittalViewPlaneNormal = sliceNormalVec.map((val) => -val);
    const sagittalViewUp = colVec.map((val) => -val);

    // Coronal View (Front View)
    const coronalViewPlaneNormal = rowVec.map((val) => -val);
    const coronalViewUp = colVec.map((val) => -val);


    // https://github.com/cornerstonejs/cornerstone3D/issues/653

    const OrientationAxis = {
        AXIAL: 'axial',
        CORONAL: 'coronal',
        SAGITTAL: 'sagittal',
        ACQUISITION: 'acquisition',
      };

    viewport0.setOrientation(
        OrientationAxis.SAGITTAL
    );  
    viewport0.setCamera({ axialViewPlaneNormal, axialViewUp })
    viewport0.setOrientation(
        {
            viewPlaneNormal: axialViewPlaneNormal,
            viewUp: axialViewUp,
       } 
   );  
    viewport0.resetCamera();
    viewport0.render();

    viewport1.setCamera({ sagittalViewPlaneNormal, sagittalViewUp });
    viewport1.resetCamera();
    viewport1.render();

    viewport2.setCamera({ coronalViewPlaneNormal, coronalViewUp });
    viewport2.resetCamera();
    viewport2.render();

}