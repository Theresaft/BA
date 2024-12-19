<script>
    // Svelte 
    import { onMount } from 'svelte';
    import { viewerAlreadySetup } from '../../stores/ViewerStore'
    import { viewerState  } from '../../stores/ViewerStore'
    import Loading from '../../single-components/Loading.svelte'
    
    // Cornerstone CORE
    import {
      init as csRenderInit, 
      RenderingEngine,
      Enums,
      volumeLoader,
      setVolumesForViewports,
      cache,
      imageLoader,
      metaData
    } from '@cornerstonejs/core';
    const { ViewportType } = Enums;
  
    // Cornerstone TOOLS
    import { init as csToolsInit,
        ToolGroupManager,
        Enums as csToolsEnums,
        StackScrollTool,
        addTool,
        segmentation,
        BrushTool,
        CrosshairsTool,
    } from '@cornerstonejs/tools';
    const { MouseBindings } = csToolsEnums;
  
    // Dicom Image Loader
    import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader';
    import cornerstoneDICOMImageLoader from '@cornerstonejs/dicom-image-loader';
    import wadors from '@cornerstonejs/dicom-image-loader/wadors';
  
    // Cornerstone adapters
    import * as cornerstoneAdapters from "@cornerstonejs/adapters";
    const { adaptersSEG, helpers } = cornerstoneAdapters;
    const { Cornerstone3D } = adaptersSEG;
    const { downloadDICOMData } = helpers;
  
    // dicom JS
    import dcmjs from "dcmjs";
  
    // dicom client
   import { api } from 'dicomweb-client';
   import { v4 as uuidv4 } from 'uuid';

    // ================================================================================
    // ================================ Properties ====================================
    // ================================================================================
    /**
     * Holds all images Blobs for raw images (e.g. t1) and segmentation labels.
     * - t1, t1km, t2, flair hold a single Blob when nifti and an array of Blobs when DICOM
     * - Labels are always niftis
     */
   export let images = {
        t1: null,
        t1km: null,
        t2: null,
        flair: null,
        labels: [],
        fileType : "",  // Corresponds to the loaded images and is either "DICOM" or "NIFTI"
    }

    export let viewerIsLoading;
  
    // ================================================================================
    // ================================= Variables ====================================
    // ================================================================================
  
  
    const toolState = {
      brushIsActive: false
    }
  
    let elementRef1 = null;
    let elementRef2 = null;
    let elementRef3 = null;
  
  
  // ================================================================================
  // ================================ Load Images ===================================
  // ================================================================================
  
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
  
    $: {
      if (images.t1) {
        console.log("loading image");
        loadImages(null, "backend");
      }
    }

    async function loadImages(files, loadingType){
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
              for (let i = 0; i < images.t1.length; i++) {
                  const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(images.t1[i]);
                  imageIds.push(imageId);
              }
              await prefetchMetadataInformation(imageIds);
              break;

          default:
              console.error("Invalid loading type:", loadingType);
              break;
      }
  
      $viewerState.referenceImageIds = imageIds
  
  
      // Define a volume in memory
      $viewerState.volumeId = uuidv4();      
  
      const volume = await volumeLoader.createAndCacheVolume($viewerState.volumeId, {
        imageIds,
      });
  
      volume.load();
  
      setVolumesForViewports(
        $viewerState.renderingEngine,
        [{ volumeId: $viewerState.volumeId }],
        [$viewerState.viewportIds[0], $viewerState.viewportIds[1], $viewerState.viewportIds[2]]
      );
  
      viewerIsLoading = false
    }
  
    // preloads imageIds metadata in memory
    async function prefetchMetadataInformation(imageIdsToPrefetch) {
      for (let i = 0; i < imageIdsToPrefetch.length; i++) {
        await cornerstoneDICOMImageLoader.wadouri.loadImage(imageIdsToPrefetch[i]).promise;
      }
    }
  
  // ================================================================================
  // ========================= Create Empty Segmentation ============================
  // ================================================================================
  
    async function addActiveSegmentation() {
      if (!$viewerState.volumeId) {
          return;
      }
  
      // Generate segmentation id
      $viewerState.segmentationId = uuidv4()
      // Add some segmentations based on the source data stack
      await addSegmentationsToState($viewerState.segmentationId);
  
    }
  
    async function addSegmentationsToState(segmentationId) {
      // Create a segmentation of the same resolution as the source data
      const derivedVolume =
          await volumeLoader.createAndCacheDerivedLabelmapVolume($viewerState.volumeId, {
              volumeId: segmentationId
          });
  
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
  
      // Add the segmentation representation to the viewport
      await segmentation.addSegmentationRepresentations($viewerState.viewportIds[0], [
          {
              segmentationId,
              type: csToolsEnums.SegmentationRepresentations.Labelmap
          }
      ]);
  
      await segmentation.addSegmentationRepresentations($viewerState.viewportIds[1], [
          {
              segmentationId,
              type: csToolsEnums.SegmentationRepresentations.Labelmap
          }
      ]);
  
      await segmentation.addSegmentationRepresentations($viewerState.viewportIds[2], [
          {
              segmentationId,
              type: csToolsEnums.SegmentationRepresentations.Labelmap
          }
      ]);
  
      return derivedVolume;
    }
  
  // ================================================================================
  // ============================ Import Segmentation ===============================
  // ================================================================================
    async function importSegmentation(files) {
        
      if (!$viewerState.volumeId) {
          return;
      }
      $viewerState.segmentationId = uuidv4()
  
      for (const file of files) {
          await readSegmentation(file, $viewerState);
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
  
    function createSegmentationRepresentation() {
      const segMap = {
          [$viewerState.viewportIds[0]]: [{ segmentationId: $viewerState.segmentationId }],
          [$viewerState.viewportIds[1]]: [{ segmentationId: $viewerState.segmentationId }],
          [$viewerState.viewportIds[2]]: [{ segmentationId: $viewerState.segmentationId }]
      };
  
      segmentation.addLabelmapRepresentationToViewportMap(segMap);
    }
  
  // ================================================================================
  // ============================ Export Segmentation ===============================
  // ================================================================================
  
  async function exportSegmentation(){
      const segmentationIds = getSegmentationIds();
      if (!segmentationIds.length) {
          return;
      }
      const active_segmentation = segmentation.state.getSegmentation($viewerState.segmentationId);
  
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
              $viewerState.viewportIds[0],
              $viewerState.segmentationId,
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
  
  // ================================================================================
  // ================================ Tool Helper ===================================
  // ================================================================================
  
  
    // Crosshair helper functions
    function getReferenceLineColor(viewportId) {
      const viewportColors = {
        [$viewerState.viewportIds[0]]: 'rgb(200, 0, 0)',
        [$viewerState.viewportIds[1]]: 'rgb(200, 200, 0)',
        [$viewerState.viewportIds[2]]: 'rgb(0, 200, 0)',
      };
  
      return viewportColors[viewportId];
    }
  
    function getReferenceLineControllable(viewportId) {
      const index = $viewerState.viewportIds.indexOf(viewportId);
      return index !== -1;
    }
  
    function getReferenceLineDraggableRotatable(viewportId) {
      const index = $viewerState.viewportIds.indexOf(viewportId);
      return index !== -1;
    }
  
    function getReferenceLineSlabThicknessControlsOn(viewportId) {
      const index = $viewerState.viewportIds.indexOf(viewportId);
      return index !== -1;
    }
  
    
    function toogleBrush(){
  
      if(toolState.brushIsActive){
        $viewerState.toolGroup.setToolPassive("CircularBrush");
        $viewerState.toolGroup.setToolActive(CrosshairsTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Primary }],
        });
      } else {
        $viewerState.toolGroup.setToolPassive(CrosshairsTool.toolName);
        $viewerState.toolGroup.setToolActive("CircularBrush", {
          bindings: [
            {
              mouseButton: MouseBindings.Primary, // Left Click
            },
          ],
        });
      }
      toolState.brushIsActive = !toolState.brushIsActive
  
    }
  
    // ================================================================================
    // =============================== Set up Viewer ==================================
    // ================================================================================
  
  
    async function setup() {
      
      // Initialization
      await csRenderInit();
      await csToolsInit();

      if(!$viewerAlreadySetup){
        dicomImageLoaderInit({ maxWebWorkers: 1 });
      }
  
      // Add tools to Cornerstone3D
      addTool(StackScrollTool);
      addTool(BrushTool);
      addTool(CrosshairsTool);

      if(!$viewerAlreadySetup){
        // Define tool groups to add the segmentation display tool to
        $viewerState.toolGroup = ToolGroupManager.createToolGroup(
            $viewerState.toolGroupId
        );
  
        /**
         * Configuration of the Tools
        */

        $viewerState.toolGroup.addTool(StackScrollTool.toolName);
    
        $viewerState.toolGroup.addToolInstance(
          'CircularBrush',
          BrushTool.toolName,
          {
            activeStrategy: 'FILL_INSIDE_CIRCLE',
          }
        );
    
        const isMobile = window.matchMedia('(any-pointer:coarse)').matches;
        $viewerState.toolGroup.addTool(CrosshairsTool.toolName, {
          getReferenceLineColor,
          getReferenceLineControllable,
          getReferenceLineDraggableRotatable,
          getReferenceLineSlabThicknessControlsOn,
          mobile: {
            enabled: isMobile,
            opacity: 0.8,
            handleRadius: 9,
          },
        });
    
        /**
         * Set Tools to active state
        */
        $viewerState.toolGroup.setToolActive(StackScrollTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Wheel }],
        });
    
        $viewerState.toolGroup.setToolActive(CrosshairsTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Primary }],
        });
      
  
        // Instantiate a rendering engine
        $viewerState.renderingEngine = new RenderingEngine($viewerState.renderingEngineId);
      }

      // Create the viewports
      const viewportInputArray = [
        {
          viewportId: $viewerState.viewportIds[0],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef1,
          defaultOptions: {
            orientation: Enums.OrientationAxis.AXIAL,
            background: [0, 0, 0],
          },
        },
        {
          viewportId: $viewerState.viewportIds[1],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef2,
          defaultOptions: {
            orientation: Enums.OrientationAxis.SAGITTAL,
            background: [0, 0, 0],
          },
        },
        {
          viewportId: $viewerState.viewportIds[2],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef3,
          defaultOptions: {
            orientation: Enums.OrientationAxis.CORONAL,
            background: [0, 0, 0],
          },
        },
      ];
      
      $viewerState.renderingEngine.setViewports(viewportInputArray);

      $viewerState.toolGroup.addViewport($viewerState.viewportIds[0], $viewerState.renderingEngineId);
      $viewerState.toolGroup.addViewport($viewerState.viewportIds[1], $viewerState.renderingEngineId);
      $viewerState.toolGroup.addViewport($viewerState.viewportIds[2], $viewerState.renderingEngineId);
      
      $viewerAlreadySetup = true
    }
  
    // Run setup on mount
    onMount(() => {
      setup();
    });
  
  
  </script>
  
  
  
  <div id="content" style="display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #000000; 	width: 100%; padding: 10px">
  
    <div style="display: flex; flex-direction: row; width: 100%;">
  
      <!-- Viewer -->
      <div style="display: flex; flex-direction: row; width: 100%;">
        <!-- Main Viewport -->
        <div 
          bind:this={elementRef1}
          style="
            flex: 1; 
            background-color: lightgray; 
            border: 2px solid white; 
            width: 33.333333%;
            aspect-ratio: 1 / 1;
            ">           
          </div>
        <!-- TODO: Style properly-->
        {#if viewerIsLoading}
          <div style="
            position: absolute; 
            flex: 1; 
            background-color: black; 
            border: 2px solid white; 
            left: 50%;   
            display: flex;
            justify-content: center;
             align-items: center

            ">
            <Loading spinnerSizePx={100}></Loading>
          </div>
        {/if}


        <!-- Small Viewports -->
        <div style="display: flex; flex-direction: column; width: 33.333333%">
          <div 
            bind:this={elementRef2}
            style="width: 100%; aspect-ratio: 1 / 1; background-color: lightgray; border: 2px solid white;">
          </div>
          <div 
            bind:this={elementRef3}
            style="width: 100%; aspect-ratio: 1 / 1; background-color: lightgray; border: 2px solid white;">
          </div>
        </div>
      </div>
  
      <!-- Sidebar with controlls -->
      <div class="sidebar">
        <div class="control-group">
          <label for="label1" class="control-label">Load Images:</label>
          <div id="label1" class="control-buttons">
            <button class="btn btn-primary" on:click={()=> loadImages(null, "cloud")}>Load Cloud Images</button>
            <input type="file" on:change={(event) => loadImages(event.target.files, "local")} webkitdirectory multiple/>
          </div>
        </div>
        <div class="control-group">
          <label for="label2" class="control-label">Create Segmentation:</label>
          <div id="label2" class="control-buttons">
            <button class="btn btn-primary" on:click={() => addActiveSegmentation()}>Start Segmentation</button>
            <button class="btn btn-primary" on:click={() => toogleBrush()}>Toggle Brush</button>
          </div>
        </div>
        <div class="control-group">
          <label for="label3" class="control-label">Import/Export Segmentation:</label>
          <div id="label3" class="control-buttons">
            <input type="file" on:change={(event) => importSegmentation(event.target.files)}  />
            <button class="btn btn-primary" on:click={() => exportSegmentation()}>Export Segmentation</button>
          </div>
        </div>
      </div>
  
    </div>
  
  </div>
  
  <style>
    /* General Sidebar Styling */
  .sidebar {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 20px;
    background-color: #f9f9f9;
    padding: 20px;
    margin-left: 10px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    font-family: Arial, sans-serif;
  }
  
  /* Control Group */
  .control-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  /* Label Styling */
  .control-label {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    margin-bottom: 5px;
  }
  
  /* Button Group */
  .control-buttons {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  
  /* Button Styling */
  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: background-color 0.3s;
    width: 200px;
  }
  
  .btn-primary {
    background-color: #007bff;
    color: white;
  }
  
  .btn-primary:hover {
    background-color: #0056b3;
  }
  
  
  </style>