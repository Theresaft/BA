/**
 * This file contains all helper functions for loading dicom or nifti images as a cornerstone volume
*/

import { get } from "svelte/store";

// Cornerstone CORE
import {
    volumeLoader,
    setVolumesForViewports,
    imageLoader,
    metaData,
    getEnabledElementByViewportId,
    getRenderingEngine
} from '@cornerstonejs/core';

// Dicom Image Loader
import cornerstoneDICOMImageLoader from '@cornerstonejs/dicom-image-loader';

// dicom client
import { api } from 'dicomweb-client';
import { v4 as uuidv4 } from 'uuid';


import wadors from '@cornerstonejs/dicom-image-loader/wadors';
import {
cornerstoneNiftiImageLoader,
createNiftiImageIdsAndCacheMetadata,
} from '@cornerstonejs/nifti-volume-loader';

import { 
  Enums as csToolsEnums,
  segmentation,
} from '@cornerstonejs/tools';


import {images, viewerState, viewerIsLoading} from "../../stores/ViewerStore"


async function createImageIDsFromCloud(){
  
    const StudyInstanceUID = '1.3.6.1.4.1.14519.5.2.1.7009.2403.334240657131972136850343327463'
    const SeriesInstanceUID = '1.3.6.1.4.1.14519.5.2.1.7009.2403.226151125820845824875394858561'
    const SOPInstanceUID = null
    const wadoRsRoot = 'https://d3t6nz73ql33tx.cloudfront.net/dicomweb'
    const client = null
    const SOP_INSTANCE_UID = '00080018';
    const SERIES_INSTANCE_UID = '0020000E';
    const studySearchOptions = {
      studyInstanceUID: StudyInstanceUID,
      seriesInstanceUID: SeriesInstanceUID,
    };

    const dicomClient = client ?? new api.DICOMwebClient({ url: wadoRsRoot, singlepart: true });

    const instances = await dicomClient.retrieveSeriesMetadata(studySearchOptions);
    const imageIds = instances.map((instanceMetaData) => {
      const seriesUID = instanceMetaData[SERIES_INSTANCE_UID]?.Value?.[0];
      if (!seriesUID) {
        throw new Error('Series Instance UID not found in metadata');
      }

      const sopUID = instanceMetaData[SOP_INSTANCE_UID]?.Value?.[0];
      if (!sopUID && !SOPInstanceUID) {
        throw new Error('SOP Instance UID not found in metadata');
      }

      const SOPInstanceUIDToUse = SOPInstanceUID || sopUID;

      const prefix = 'wadors:';
      const imageId =
        prefix +
        wadoRsRoot +
        '/studies/' +
        StudyInstanceUID +
        '/series/' +
        seriesUID +
        '/instances/' +
        SOPInstanceUIDToUse +
        '/frames/1';

      wadors.metaDataManager.add(imageId, instanceMetaData );
      return imageId;
    });

    return imageIds;
  }

  let volume = null

  export async function loadImages(files, loadingType, modality="t1"){
    const currentViewerState = get(viewerState);
    const axialViewportID = currentViewerState.viewportIds[0] 
    const sagitalViewportID = currentViewerState.viewportIds[1]
    const coronalViewportID = currentViewerState.viewportIds[2]


    let imageIds = []

    switch (loadingType) {
        case "local":
            for (let i = 0; i < files.length; i++) {
                const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(files[i]);
                imageIds.push(imageId);
            }
            await prefetchMetadataInformation(imageIds);
            break;

        case "cloud":
            imageIds = await createImageIDsFromCloud();
            break;

        case "backend":
            
            const current_images = get(images)

            for (let i = 0; i < current_images[modality].length; i++) {
                const imageSlice = current_images[modality]
                const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(imageSlice[i]);
                imageIds.push(imageId);
            }
            await prefetchMetadataInformation(imageIds);
            break;

        default:
            console.error("Invalid loading type:", loadingType);
            break;
    }

    // From tools/examples/local
    const {
      pixelRepresentation,
      bitsAllocated,
      bitsStored,
      highBit,
      photometricInterpretation,
    } = metaData.get('imagePixelModule', imageIds[22]);

    const voiLutModule = metaData.get('voiLutModule', imageIds[22]);
    const sopCommonModule = metaData.get('sopCommonModule', imageIds[22]);
    const transferSyntax = metaData.get('transferSyntax', imageIds[22]);

    console.log("voiLutModule: " + JSON.stringify(voiLutModule));
    // console.log("sopCommonModule: " + JSON.stringify(sopCommonModule));
    // console.log("transferSyntax: " + JSON.stringify(transferSyntax));
    
    // console.log("pixelRepresentation: " + JSON.stringify(pixelRepresentation));
    // console.log("bitsAllocated: " + JSON.stringify(bitsAllocated));
    // console.log("bitsStored: " + JSON.stringify(bitsStored));
    // console.log("highBit: " + JSON.stringify(highBit));
    console.log("photometricInterpretation: " + JSON.stringify(photometricInterpretation));
    


    const imagePlaneModule = metaData.get('imagePlaneModule', imageIds[22]);
    Object.entries(imagePlaneModule).forEach(([key, value]) => {
      console.log(`${key}: ${JSON.stringify(value)}`);
    });
    

    viewerState.update(state => ({
        ...state,
        referenceImageIds: imageIds
    }));

    const volumeID = uuidv4();


    // Define a volume in memory
    viewerState.update(state => ({
        ...state,
        volumeId: volumeID
    }));    

    volume = await volumeLoader.createAndCacheVolume(volumeID, {
      imageIds,
    });
    


    volume.load();

    // console.log("$viewerState.renderingEngine.getViewport loaded: " + JSON.stringify($viewerState.renderingEngine.getViewport($viewerState.viewportIds[0])));
    // const IOP = imagePlaneModule.imageOrientationPatient

    // const rowVec = [IOP[0],IOP[1],IOP[2]]
    // const colVec = [IOP[3],IOP[4],IOP[5]]

    // setCamera(rowVec, colVec, axialViewportID, sagitalViewportID, coronalViewportID)       

    setVolumesForViewports(
        currentViewerState.renderingEngine,
      [{ volumeId: volumeID }],
      [axialViewportID, sagitalViewportID, coronalViewportID]
    );


    // Add segmentations to viewport whenever a new base image is loaded
    // We want to show the segmentation whenever the base image is changed
    // There could be another way to do this
    const segmentationId = currentViewerState.segmentationId

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

    viewerIsLoading.set(false)  


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
        volumeId: volumeID
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