<script>
    // Svelte 
    import { onMount } from 'svelte';
    
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
  
  
    // ================================================================================
    // ================================= Variables ====================================
    // ================================================================================
  
    const state = {
      renderingEngine: null,
      renderingEngineId: "MY_RENDERING_ENGINE_ID",
      toolGroup: null,
      toolGroupId: "MY_TOOL_GROUP_ID",
      viewportIds: ["CT_AXIAL", "CT_SAGITTAL", "CT_CORONAL"],
      volumeId: "",
      segmentationId: "",
      referenceImageIds: [],
      skipOverlapping: false,
      segImageIds: [],
    };
  
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
  
  
    async function loadImages(files, localLoading){
      let imageIds = []
  
      if(localLoading){
        for (let i = 0; i < files.length; i++) {
          const imageId = cornerstoneDICOMImageLoader.wadouri.fileManager.add(files[i]);
          imageIds.push(imageId)
        }
        await prefetchMetadataInformation(imageIds);
      } else {
        imageIds = await createImageIDsFromCloud()
      }
  
      state.referenceImageIds = imageIds
  
  
      // Define a volume in memory
      state.volumeId = 'myVolume';
  
      const volume = await volumeLoader.createAndCacheVolume(state.volumeId, {
        imageIds,
      });
  
      volume.load();
  
      setVolumesForViewports(
        state.renderingEngine,
        [{ volumeId: state.volumeId }],
        [state.viewportIds[0], state.viewportIds[1], state.viewportIds[2]]
      );
  
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
      if (!state.volumeId) {
          return;
      }
  
      // Generate segmentation id
      state.segmentationId = "NEW_SEG_ID:1"
      // Add some segmentations based on the source data stack
      await addSegmentationsToState(state.segmentationId);
  
    }
  
    async function addSegmentationsToState(segmentationId) {
      // Create a segmentation of the same resolution as the source data
      const derivedVolume =
          await volumeLoader.createAndCacheDerivedLabelmapVolume(state.volumeId, {
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
      await segmentation.addSegmentationRepresentations(state.viewportIds[0], [
          {
              segmentationId,
              type: csToolsEnums.SegmentationRepresentations.Labelmap
          }
      ]);
  
      await segmentation.addSegmentationRepresentations(state.viewportIds[1], [
          {
              segmentationId,
              type: csToolsEnums.SegmentationRepresentations.Labelmap
          }
      ]);
  
      await segmentation.addSegmentationRepresentations(state.viewportIds[2], [
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
        
      if (!state.volumeId) {
          return;
      }
      state.segmentationId = "SEG_ID_2"
  
      for (const file of files) {
          await readSegmentation(file, state);
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
          [state.viewportIds[0]]: [{ segmentationId: state.segmentationId }],
          [state.viewportIds[1]]: [{ segmentationId: state.segmentationId }],
          [state.viewportIds[2]]: [{ segmentationId: state.segmentationId }]
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
      const active_segmentation = segmentation.state.getSegmentation(state.segmentationId);
  
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
              state.viewportIds[0],
              state.segmentationId,
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
        [state.viewportIds[0]]: 'rgb(200, 0, 0)',
        [state.viewportIds[1]]: 'rgb(200, 200, 0)',
        [state.viewportIds[2]]: 'rgb(0, 200, 0)',
      };
  
      return viewportColors[viewportId];
    }
  
    function getReferenceLineControllable(viewportId) {
      const index = state.viewportIds.indexOf(viewportId);
      return index !== -1;
    }
  
    function getReferenceLineDraggableRotatable(viewportId) {
      const index = state.viewportIds.indexOf(viewportId);
      return index !== -1;
    }
  
    function getReferenceLineSlabThicknessControlsOn(viewportId) {
      const index = state.viewportIds.indexOf(viewportId);
      return index !== -1;
    }
  
    
    function toogleBrush(){
  
      if(toolState.brushIsActive){
        state.toolGroup.setToolPassive("CircularBrush");
        state.toolGroup.setToolActive(CrosshairsTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Primary }],
        });
      } else {
        state.toolGroup.setToolPassive(CrosshairsTool.toolName);
        state.toolGroup.setToolActive("CircularBrush", {
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
      dicomImageLoaderInit({ maxWebWorkers: 1 });
  
      // Add tools to Cornerstone3D
      addTool(StackScrollTool);
      addTool(BrushTool);
      addTool(CrosshairsTool);
  
      // Define tool groups to add the segmentation display tool to
      state.toolGroup = ToolGroupManager.createToolGroup(
          state.toolGroupId
      );
  
      /**
       * Configuration of the Tools
      */
      state.toolGroup.addTool(StackScrollTool.toolName);
  
      state.toolGroup.addToolInstance(
        'CircularBrush',
        BrushTool.toolName,
        {
          activeStrategy: 'FILL_INSIDE_CIRCLE',
        }
      );
  
      const isMobile = window.matchMedia('(any-pointer:coarse)').matches;
      state.toolGroup.addTool(CrosshairsTool.toolName, {
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
      state.toolGroup.setToolActive(StackScrollTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Wheel }],
      });
  
      state.toolGroup.setToolActive(CrosshairsTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Primary }],
      });
  
  
      // Instantiate a rendering engine
      state.renderingEngine = new RenderingEngine(state.renderingEngineId);
  
      // Create the viewports
      const viewportInputArray = [
        {
          viewportId: state.viewportIds[0],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef1,
          defaultOptions: {
            orientation: Enums.OrientationAxis.AXIAL,
            background: [0, 0, 0],
          },
        },
        {
          viewportId: state.viewportIds[1],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef2,
          defaultOptions: {
            orientation: Enums.OrientationAxis.SAGITTAL,
            background: [0, 0, 0],
          },
        },
        {
          viewportId: state.viewportIds[2],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef3,
          defaultOptions: {
            orientation: Enums.OrientationAxis.CORONAL,
            background: [0, 0, 0],
          },
        },
      ];
  
      state.renderingEngine.setViewports(viewportInputArray);
  
      state.toolGroup.addViewport(state.viewportIds[0], state.renderingEngineId);
      state.toolGroup.addViewport(state.viewportIds[1], state.renderingEngineId);
      state.toolGroup.addViewport(state.viewportIds[2], state.renderingEngineId);
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
            <button class="btn btn-primary" on:click={()=> loadImages(null, false)}>Load Cloud Images</button>
            <input type="file" on:change={(event) => loadImages(event.target.files, true)} webkitdirectory multiple/>
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