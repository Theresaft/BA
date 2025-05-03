/**
 * This file contains all helper functions for importing and exporting a segmentation object in cornerstone
 * It is no longer used since we are doing everything with the backend
 * Still exists for reference
*/

// Svelte 
import { get } from "svelte/store";

// Cornerstone CORE
import {
    cache,
    imageLoader,
    metaData
} from '@cornerstonejs/core';

// Cornerstone TOOLS
import { 
    Enums as csToolsEnums,
    segmentation,
} from '@cornerstonejs/tools';

// Dicom Image Loader
import cornerstoneDICOMImageLoader from '@cornerstonejs/dicom-image-loader';


// Cornerstone adapters
import * as cornerstoneAdapters from "@cornerstonejs/adapters";
const { adaptersSEG, helpers } = cornerstoneAdapters;
const { Cornerstone3D } = adaptersSEG;
const { downloadDICOMData } = helpers;

// dicom JS
import dcmjs from "dcmjs";

import { v4 as uuidv4 } from 'uuid';

import {viewerState} from "../../stores/ViewerStore"


// ================================================================================
// ============================ Import Segmentation ===============================
// ================================================================================
export async function importSegmentation(files) {

    const currentViewerState = get(viewerState)

      
    if (!currentViewerState.imageVolumeID) {
        return;
    }

    const segmentationId =  uuidv4()

    viewerState.update(state => ({
        ...state,
        segmentationId: segmentationId
    }));

    for (const file of files) {
        await readSegmentation(file, currentViewerState);
    }
    createSegmentationRepresentation();

  }

  async function readSegmentation(file, state) {

    const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(file);
    const image = await imageLoader.loadAndCacheImage(imageId);

    if (!image) {
        return;
    }

    const instance = metaData.get("instance", imageId);

    if (instance.Modality !== "SEG") {
        console.error("This is not segmentation: " + file.name);
        return;
    }

    const arrayBuffer = image.data.byteArray.buffer;

    await loadSegmentation(arrayBuffer, state);      

  }

  async function loadSegmentation(arrayBuffer, state) {
    const { referenceImageIds, skipOverlapping, segmentationId } = state;

    console.log("Generating Tool State");
    

    const generateToolState =
        await Cornerstone3D.Segmentation.generateToolState(
            referenceImageIds,
            arrayBuffer,
            metaData,
            skipOverlapping // Removed object here
        );

    if (generateToolState.labelmapBufferArray.length !== 1) {
        alert(
            "Overlapping segments in your segmentation are not supported yet. You can turn on the skipOverlapping option but it will override the overlapping segments."
        );
        return;
    }

    console.log("Generating Tool State");

    await createSegmentation(state);

    const active_segmentation = segmentation.state.getSegmentation(segmentationId);

    const { imageIds } = active_segmentation.representationData.Labelmap;
    const derivedSegmentationImages = imageIds.map((imageId) =>
        cache.getImage(imageId)
    );

    const volumeScalarData = new Uint8Array(
        generateToolState.labelmapBufferArray[0]
    );

    for (let i = 0; i < derivedSegmentationImages.length; i++) {
        const voxelManager = derivedSegmentationImages[i].voxelManager;
        const scalarData = voxelManager.getScalarData();
        scalarData.set(
            volumeScalarData.slice(
                i * scalarData.length,
                (i + 1) * scalarData.length
            )
        );
        voxelManager.setScalarData(scalarData);
    }

  }

  async function createSegmentation(state) {
    const { referenceImageIds, segmentationId } = state;

    const derivedSegmentationImages =
        await imageLoader.createAndCacheDerivedLabelmapImages(
            referenceImageIds
        );

    const derivedSegmentationImageIds = derivedSegmentationImages.map(
        image => image.imageId
    );

    segmentation.addSegmentations([
        {
            segmentationId,
            representation: {
                type: csToolsEnums.SegmentationRepresentations.Labelmap,
                data: {
                    imageIds: derivedSegmentationImageIds
                }
            }
        }
    ]);
  }

  function createSegmentationRepresentation(segmentationId) {

    const currentViewerState = get(viewerState)

    const segMap = {
        [currentViewerState.viewportIds[0]]: [{ segmentationId: segmentationId }],
        [currentViewerState.viewportIds[1]]: [{ segmentationId: segmentationId }],
        [currentViewerState.viewportIds[2]]: [{ segmentationId: segmentationId }]
    };

    segmentation.addLabelmapRepresentationToViewportMap(segMap);
  }

// ================================================================================
// ============================ Export Segmentation ===============================
// ================================================================================

export async function exportSegmentation(){

    const currentViewerState = get(viewerState)


    const segmentationIds = getSegmentationIds();
    if (!segmentationIds.length) {
        return;
    }
    const active_segmentation = segmentation.state.getSegmentation(currentViewerState.segmentationId);

    const { imageIds } = active_segmentation.representationData.Labelmap;

    const segImages = imageIds.map((imageId) => cache.getImage(imageId));
    const referencedImages = segImages.map((image) =>
        cache.getImage(image.referencedImageId)
    );

    const labelmaps2D = [];

    let z = 0;

    for (const segImage of segImages) {
        const segmentsOnLabelmap = new Set();
        const pixelData = segImage.getPixelData();
        const { rows, columns } = segImage;

        for (let i = 0; i < pixelData.length; i++) {
            const segment = pixelData[i];
            if (segment !== 0) {
                segmentsOnLabelmap.add(segment);
            }
        }

        labelmaps2D[z++] = {
            segmentsOnLabelmap: Array.from(segmentsOnLabelmap),
            pixelData,
            rows,
            columns
        };
    }

    const allSegmentsOnLabelmap = labelmaps2D.map(
        labelmap => labelmap.segmentsOnLabelmap
    );

    const labelmap3D = {
        segmentsOnLabelmap: Array.from(new Set(allSegmentsOnLabelmap.flat())),
        metadata: [],
        labelmaps2D
    };

    labelmap3D.segmentsOnLabelmap.forEach((segmentIndex) => {
        const color = segmentation.config.color.getSegmentIndexColor(
            currentViewerState.viewportIds[0],
            currentViewerState.segmentationId,
            segmentIndex
        );
        const RecommendedDisplayCIELabValue = dcmjs.data.Colors.rgb2DICOMLAB(
            color.slice(0, 3).map(value => value / 255)
        ).map((value) => Math.round(value));

        const segmentMetadata = {
            SegmentNumber: segmentIndex.toString(),
            SegmentLabel: `Segment ${segmentIndex}`,
            SegmentAlgorithmType: "MANUAL",
            SegmentAlgorithmName: "OHIF Brush",
            RecommendedDisplayCIELabValue,
            SegmentedPropertyCategoryCodeSequence: {
                CodeValue: "T-D0050",
                CodingSchemeDesignator: "SRT",
                CodeMeaning: "Tissue"
            },
            SegmentedPropertyTypeCodeSequence: {
                CodeValue: "T-D0050",
                CodingSchemeDesignator: "SRT",
                CodeMeaning: "Tissue"
            }
        };
        labelmap3D.metadata[segmentIndex] = segmentMetadata;
    });

    const generatedSegmentation =
        Cornerstone3D.Segmentation.generateSegmentation(
            referencedImages,
            labelmap3D,
            metaData
        );

    downloadDICOMData(generatedSegmentation.dataset, "mySEG.dcm");
  }


  function getSegmentationIds() {
      return segmentation.state
          .getSegmentations()
          .map(x => x.segmentationId);
  }