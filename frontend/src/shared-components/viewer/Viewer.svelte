<script>
    // Svelte 
    import { onMount } from 'svelte';
    import { get } from "svelte/store";
    import { tick } from 'svelte';

    import Loading from '../../single-components/Loading.svelte'
    import CrossHairSymbol from '../svg/CrossHairSymbol.svelte';
    import EraserSymbol from '../svg/EraserSymbol.svelte';
    import RulerSymbol from '../svg/RulerSymbol.svelte';
    import {images, viewerIsLoading, viewerState, viewerAlreadySetup, segmentationLoaded, labelState} from "../../stores/ViewerStore"
    import {UserSettings} from "../../stores/Store"
    import {getMaxPixelValue} from "../../shared-components/viewer/image-loader"
    import {resetSegmentationStyles} from "../../shared-components/viewer/segmentation"

    // Cornerstone CORE
    import {
      init as csRenderInit, 
      RenderingEngine,
      Enums,
      metaData
    } from '@cornerstonejs/core';
    const { ViewportType } = Enums;
  
    // Cornerstone TOOLS
    import { init as csToolsInit,
        ToolGroupManager,
        Enums as csToolsEnums,
        StackScrollTool,
        addTool,
        BrushTool,
        CrosshairsTool,
        ZoomTool,
        PanTool,
        WindowLevelTool,
        LengthTool,
        HeightTool,
        EraserTool,
        synchronizers,
        SynchronizerManager
    } from '@cornerstonejs/tools';
    const { MouseBindings, KeyboardBindings } = csToolsEnums;
    const { createVOISynchronizer } = synchronizers;
  
    // Dicom Image Loader
    import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader';

    
   import {loadImages} from "./image-loader"
   import {addActiveSegmentation, addSegmentationRepresentations, removeAllSegmentationRepresentations} from "./segmentation"
   import {getReferenceLineColor, 
      getReferenceLineControllable, 
      getReferenceLineDraggableRotatable, 
      getReferenceLineSlabThicknessControlsOn,
  } from "./tool"
  import ClassLabel from './ClassLabel.svelte';

    // ================================================================================
    // ================================= Variables ====================================
    // ================================================================================
  
    // Toolname of the primary tool (left-click-tool)
    let activePrimaryTool = ""

    let colormaps = ["Grayscale", "rainbow", "Warm to Cool", "Black, Orange and White"]; 
    let selectedColormap = colormaps[0]; // Default selection


  
    let elementRef1 = null;
    let elementRef2 = null;
    let elementRef3 = null;
  
  
    $: {
        if ($images.t1) {

          // Load either currently selected modality back to the viewer or t1 when images are first loaded
          (async () => { 

              const modality =  get(viewerState).currentlyDisplayedModality ||"t1" // Note: We're using get() here so that the reactive statement wont react again on updating this value

              await loadImages(modality);

              // Load segmentation when it is first loaded. Otherwise only readd segmentation representation (e.g. on page change)
              if(!get(segmentationLoaded)){
                addActiveSegmentation();
                segmentationLoaded.set(true)
              } else {
                removeAllSegmentationRepresentations()
                addSegmentationRepresentations()
              }
              
          })();

        }
    }

    // ================================================================================
    // ===================================== Buttons ==================================
    // ================================================================================

    function changeColormap(event) {
      selectedColormap = event.target.value;
      
      // Rerender all viewports with new colormap
      const renderingEngine = $viewerState.renderingEngine
      
      for(const viewportID of $viewerState.viewportIds){
        console.log("viewportID: " + viewportID);
        
        const viewport = renderingEngine.getViewport(viewportID)
        viewport.setProperties({ colormap: { name: selectedColormap } });
        viewport.render();
      }
    }

    async function resetViewer(){
      const renderingEngine = $viewerState.renderingEngine

      // Calculate voiRange for window leveling
      let voiRange
      if($UserSettings["minMaxWindowLeveling"]){
        const maxPixelValue = getMaxPixelValue($viewerState.currentlyDisplayedModality)
        voiRange = { lower: 0, upper: maxPixelValue };
      } else {
        // Calculate lower and upper bound for window leveling based on window center and window width from dicom tags
        const voiLutModule = metaData.get('voiLutModule',  $viewerState.referenceImageIds[0]);
        const windowCenter = voiLutModule.windowCenter[0]; 
        const windowWidth = voiLutModule.windowWidth[0];   
        const lower = windowCenter - windowWidth / 2.0;
        const upper = windowCenter + windowWidth / 2.0;
        voiRange = { lower, upper };
      }

      // Reset segmentation styles
      labelState.update(labels =>
        labels.map(label => ({
          ...label,
          opacity: 50,
          isVisible: true
        }))
      );
      await tick(); // Wait for DOM + reactive updates
      resetSegmentationStyles()

      // TODO: Reset Tool Annotations

      for(const viewportID of $viewerState.viewportIds){
        const viewport = renderingEngine.getViewport(viewportID)

        // Reset the camera
        viewport.resetCamera();

        // Reset the windowleveling
        viewport.setProperties({ voiRange: voiRange });
        viewport.render();
      }

    }

    async function changeModality(modality){
      await loadImages(modality)

      // Readding segmentation reprasentation, so that it is displayed in front
      removeAllSegmentationRepresentations()
      addSegmentationRepresentations()
    }

    // ================================================================================
    // =============================== Tool Activation functions ======================
    // ================================================================================

    // TODO: Refactor and move to tool.js
    // -> Create one dynamic function: activatePrimaryTool(toolname)

    function activateCrosshairTool(){

      if(activePrimaryTool == CrosshairsTool.toolName){
        return
      }

      // Set the new tool active
      $viewerState.toolGroup.setToolActive(CrosshairsTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Primary, // Left Click
          },
        ],
      });

      // Set the old tool passive
      $viewerState.toolGroup.setToolPassive(activePrimaryTool);

      activePrimaryTool = CrosshairsTool.toolName
    }

    function activateLengthTool(){

      if(activePrimaryTool == LengthTool.toolName){
        activateCrosshairTool()
        return
      }


      // Set the new tool active
      $viewerState.toolGroup.setToolActive(LengthTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Primary, // Left Click
          },
        ],
      });

      // Set the old tool passive
      $viewerState.toolGroup.setToolPassive(activePrimaryTool);

      activePrimaryTool = LengthTool.toolName

    }


    function activateEraserTool(){

      if(activePrimaryTool == EraserTool.toolName){
        activateCrosshairTool()
        return
      }


      // Set the new tool active
      $viewerState.toolGroup.setToolActive(EraserTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Primary, // Left Click
          },
        ],
      });

      // Set the old tool passive
      $viewerState.toolGroup.setToolPassive(activePrimaryTool);

      activePrimaryTool = EraserTool.toolName

    }

    function activateWindowLevelTool(){
      if(activePrimaryTool == WindowLevelTool.toolName){
        activateCrosshairTool()
        return
      }


      // Set the new tool active
      $viewerState.toolGroup.setToolActive(WindowLevelTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Primary, // Left Click
          },
        ],
      });

      // Set the old tool passive
      $viewerState.toolGroup.setToolPassive(activePrimaryTool);

      activePrimaryTool = WindowLevelTool.toolName
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
      addTool(ZoomTool)
      addTool(PanTool); // Pan Tool = Tool that moves the image
      addTool(WindowLevelTool); 
      addTool(LengthTool);
      addTool(EraserTool);

      if(!$viewerAlreadySetup){
        // Define tool groups to add the segmentation display tool to
        $viewerState.toolGroup = ToolGroupManager.createToolGroup(
            $viewerState.toolGroupId
        );
  
        /**
         * Configuration of the Tools
        */

        // Stack Scroll Tool
        $viewerState.toolGroup.addTool(StackScrollTool.toolName);

        // Zoom Tool
        $viewerState.toolGroup.addTool(ZoomTool.toolName);

        // Pan Tool
        $viewerState.toolGroup.addTool(PanTool.toolName);

        // Window Level Tool WindowLevelTool
        $viewerState.toolGroup.addTool(WindowLevelTool.toolName);

        // Length measurement tool (ruler)
        $viewerState.toolGroup.addTool(LengthTool.toolName);

        // Eraser Tool
        $viewerState.toolGroup.addTool(EraserTool.toolName);



        // Brush Tool
        $viewerState.toolGroup.addToolInstance(
          'CircularBrush',
          BrushTool.toolName,
          {
            activeStrategy: 'FILL_INSIDE_CIRCLE',
          }
        );
    
        // Crosshair Tool
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
         * --------- Set Tools to active state --------- 
        */

        activePrimaryTool = CrosshairsTool.toolName

        $viewerState.toolGroup.setToolActive(CrosshairsTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Primary }], // Left click
        });   

        $viewerState.toolGroup.setToolActive(StackScrollTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Wheel }], // Wheel scroll ;)
        });     

        $viewerState.toolGroup.setToolActive(ZoomTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Secondary }], // Right click
        });

        $viewerState.toolGroup.setToolActive(PanTool.toolName, {
          bindings: [{ mouseButton: MouseBindings.Auxiliary }], // Mouse Wheel click
        });

        $viewerState.toolGroup.setToolActive(WindowLevelTool.toolName, {
          bindings: [
            {
              mouseButton: MouseBindings.Primary, // Shift Left click
              modifierKey: KeyboardBindings.Shift,
            },
          ], 
        });
      
        /**
         * --------- Passive Tools --------- 
        */
      
        $viewerState.toolGroup.setToolPassive(HeightTool.toolName);
        $viewerState.toolGroup.setToolPassive(EraserTool.toolName);
      
  
        // Instantiate a rendering engine
        $viewerState.renderingEngine = new RenderingEngine($viewerState.renderingEngineId);

        // Create synchronizers
        createVOISynchronizer($viewerState.voiSynchronizerId, {
          syncInvertState: false,
          syncColormap: false,
        });
      }






      /**
       * ------- This is an experimantel section ----------
       * We calculate the viewplanenormal and viewup for each camera (axial, sagtial, coronal) based on Image Orientation (Patient)
       * viewPlaneNormal -> defines camera movement
       * viewUp -> defines camera rotation
       */

      // Extract row and column vectors
      // Example Image Orientation (Patient)
      const rowVec = [0.109069408251767, 0.976162325741373, -0.18764588454534];
      const colVec = [-0.0369905981086, -0.18465554846232, -0.98210693107911];

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

      // -----------------------------------------------------------


      // Create the viewports
      const viewportInputArray = [
        {
          viewportId: $viewerState.viewportIds[0],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef1,
          defaultOptions: {
            orientation: Enums.OrientationAxis.AXIAL, 
            background: [0, 0, 0], // black
            // orientation: {
            //   viewUp: axialViewUp,
            //   viewPlaneNormal: axialViewPlaneNormal,
            // }
          },
        },
        {
          viewportId: $viewerState.viewportIds[1],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef2,
          defaultOptions: {
            orientation: Enums.OrientationAxis.SAGITTAL,
            background: [0, 0, 0], // black
            // orientation: {
            //   viewUp: sagittalViewUp,
            //   viewPlaneNormal: sagittalViewPlaneNormal,
            // },
          },
        },
        {
          viewportId: $viewerState.viewportIds[2],
          type: ViewportType.ORTHOGRAPHIC,
          element: elementRef3,
          defaultOptions: {
            orientation: Enums.OrientationAxis.CORONAL,
            background: [0, 0, 0], // black
            // orientation: {
            //   viewUp: coronalViewUp,
            //   viewPlaneNormal: coronalViewPlaneNormal,
            // },
          },
        },
      ];
      
      $viewerState.renderingEngine.setViewports(viewportInputArray);

      $viewerState.toolGroup.addViewport($viewerState.viewportIds[0], $viewerState.renderingEngineId);
      $viewerState.toolGroup.addViewport($viewerState.viewportIds[1], $viewerState.renderingEngineId);
      $viewerState.toolGroup.addViewport($viewerState.viewportIds[2], $viewerState.renderingEngineId);

      // Add viewports to synchronizer
      const synchronizer = SynchronizerManager.getSynchronizer($viewerState.voiSynchronizerId);
      const renderingEngineID = $viewerState.renderingEngineId

      for(const viewportID of $viewerState.viewportIds){
        synchronizer.add({
          renderingEngineId: renderingEngineID,
          viewportId : viewportID
        });
      }

      
      $viewerAlreadySetup = true
    }
  
    // Run setup on mount
    onMount(() => {
      setup();
    });
  
    function disableRightClick(event) {
      event.preventDefault();
    }
  
  </script>
  
  
<div class="viewer-container">

  <div class="tool-bar">

    <div class="primary-tools">
      <button  
        class="tool {activePrimaryTool === CrosshairsTool.toolName ? 'active' : ''}" 
        on:click={activateCrosshairTool}>
        <CrossHairSymbol/>
      </button>

      <button 
        class="tool {activePrimaryTool === LengthTool.toolName ? 'active' : ''}" 
        on:click={activateLengthTool}>
        <RulerSymbol/>
      </button>

      <button 
        class="tool {activePrimaryTool === EraserTool.toolName ? 'active' : ''}" 
        on:click={activateEraserTool}>
        <EraserSymbol/>
      </button>

      <button 
        class="tool {activePrimaryTool === WindowLevelTool.toolName ? 'active' : ''}" 
        on:click={activateWindowLevelTool}>
        W
      </button>
    </div>

    <div class="colormap-container">
      <span class="color-map-label">Colormaps: </span>
      <select bind:value={selectedColormap} on:change={changeColormap}>
        {#each colormaps as colormap}
          <option value={colormap}>{colormap}</option>
        {/each}
      </select>
    </div>

  </div>

  <div class="viewer" role="presentation" on:contextmenu={disableRightClick}> 
    <!-- Main Viewport -->
    <div 
      bind:this={elementRef1}
      class="viewport1">  

      {#if $viewerIsLoading}
        <div class="loading-container">
          <Loading spinnerSizePx={70}></Loading>
        </div>
      {/if}

    </div>


    <!-- Small Viewports -->
    <div 
      bind:this={elementRef2}
      class="viewport2">

      {#if $viewerIsLoading}
        <div class="loading-container">
          <Loading spinnerSizePx={35}></Loading>
        </div>
      {/if}

    </div>


    <div 
      bind:this={elementRef3}
      class="viewport3">

      {#if $viewerIsLoading}
        <div class="loading-container">
          <Loading spinnerSizePx={35}></Loading>
        </div>
      {/if}

    </div>


  </div>

  <div class="bottom-bar"> 
    <div class="label-button-container"> 
      {#each $labelState as classLabel}
        <ClassLabel classLabel={classLabel} />
      {/each}
    </div>
  </div>

  <div class="sidebar">    
    <button class="modality-button" on:click={async () => changeModality("t1")}>T1</button>
    <button class="modality-button" on:click={async () => changeModality("t1km")}>T1km</button>
    <button class="modality-button" on:click={async () => changeModality("t2")}>T2</button>
    <button class="modality-button" on:click={async () => changeModality("flair")}>Flair</button>
  </div>

  <div class="settings-container"> 
    <button class="settings-button" on:click={() => resetViewer()}>R</button>
    <button class="settings-button">I</button> 
    <button class="settings-button">C</button>
    <button class="settings-button">D</button>
  </div>

</div>
  
  
  <style>
    /* General Sidebar Styling */
    button {
      all: unset; /* Resets all inherited/global styles */
    }

    .viewer-container {
      display: grid;
      grid-template-columns: auto 150px;
      grid-template-rows: 40px auto 65px;
      grid-column-gap: 0px;
      grid-row-gap: 0px;
      background-color: black;
      width: 100%;  
      height: 100%; 
      padding: 10px 10px 0px 10px;
      box-sizing: border-box;
    }

    .tool-bar{
      grid-area: 1 / 1 / 2 / 2;
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      margin: 0px 10px;
    }

    .viewer{ 
      display: grid; 
      grid-area: 2 / 1 / 3 / 2; 
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(2, 1fr);
      grid-column-gap: 0px;
      grid-row-gap: 0px;
      box-sizing: border-box;
      border: 1px solid white; 
      border-radius: 3px;
    }

    .viewport1{
      grid-area: 1 / 1 / 3 / 3;
      background-color: lightgray; 
      border: 2px solid white; 
      box-sizing: border-box;
      position: relative;
    }

    .viewport2 { 
      grid-area: 1 / 3 / 2 / 4;
      background-color: lightgray; 
      border: 2px solid white;
      box-sizing: border-box;
      position: relative; 
    }

    .viewport3 { 
      grid-area: 2 / 3 / 3 / 4;
      background-color: lightgray; 
      border: 2px solid white;
      box-sizing: border-box;
      position: relative; 
    }

    .loading-container {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }

    .sidebar { 
      grid-area: 2 / 2 / 3 / 3; 
      display: flex;
      flex-direction: column;
      justify-content: space-evenly;
      align-items: center;
      background-color: black;
    }

    .bottom-bar{
      grid-area: 3 / 1 / 4 / 2; 
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      background-color: black;
    }



    .settings-container {
      grid-area: 3 / 2 / 4 / 3; 
      background-color: black;
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: space-evenly;
    }

    .label-button-container{
      display: flex;
      gap: 10px;
      margin: 0px 10px;
    }

    .primary-tools{
      display: flex;
      flex-direction: row;
      gap: 15px;
    }
    .tool{
      width: 30px;
      height: 30px;
      border: 1px solid white;
      border-radius: 3px;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .tool:hover {
      /* border-color: var(--button-color-preview-hover);
      color: var(--button-color-preview-hover) ; */
      background-color: var(--button-color-preview-hover);
    }

    .tool.active {
      /* border-color: var(--button-color-preview);
      color: var(--button-color-preview) ; */
      background-color: var(--button-color-preview);
    }

    .colormap-container {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .color-map-label {
      font-weight: bold;
    }

    select {
      padding: 5px;
      border-radius: 3px;
      border: 1px solid white;
      color: white;
      background-color: black;
    }

    .modality-button{
      background-color: black;
      width: 100px;
      height: 100px;
      text-align: center;
      cursor: pointer;
      border: 2px solid white;
      border-radius: 3px;
    }

    .settings-button{
      background-color:darkgreen;
      width: 30px;
      height: 30px;
      text-align: center;
    }

  
  
  
  </style>