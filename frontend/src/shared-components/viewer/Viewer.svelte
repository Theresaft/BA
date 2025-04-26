<script>
  // Svelte 
  import { createEventDispatcher, onMount, onDestroy } from "svelte"
  import { get } from "svelte/store";
  import { tick } from 'svelte';

  import Loading from '../../single-components/Loading.svelte'
  import CrossHairSymbol from '../svg/CrossHairSymbol.svelte';
  import EraserSymbol from '../svg/EraserSymbol.svelte';
  import RulerSymbol from '../svg/RulerSymbol.svelte';
  import WindowLevelingSymbol from "../svg/WindowLevelingSymbol.svelte";
  import ResetViewerIcon from "../svg/ResetViewerIcon.svelte";
  import InfoIcon from "../svg/InfoIcon.svelte";
  import {images, viewerIsLoading, viewerState, viewerAlreadySetup, segmentationLoaded, labelState, resetWindowLeveling, resetImageStore} from "../../stores/ViewerStore"
  import {UserSettings} from "../../stores/Store"
  import {resetSegmentationStyles} from "../../shared-components/viewer/segmentation"
   

  // Cornerstone CORE
  import {
    init as csRenderInit, 
    RenderingEngine,
    Enums,
    utilities
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
      SynchronizerManager,
      annotation
  } from '@cornerstonejs/tools';
  const { MouseBindings, KeyboardBindings } = csToolsEnums;
  const { createVOISynchronizer } = synchronizers;

  // Dicom Image Loader
  import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader';

    
  import {loadImages} from "./image-loader"
  import {addActiveSegmentation, addSegmentationRepresentations, removeAllSegmentationRepresentations } from "./segmentation"
  import {getReferenceLineColor, 
    getReferenceLineControllable, 
    getReferenceLineDraggableRotatable, 
    getReferenceLineSlabThicknessControlsOn,
  } from "./tool"
  import ClassLabel from './ClassLabel.svelte';

  // ================================================================================
  // ================================= Variables ====================================
  // ================================================================================

  let colormaps = ["Grayscale", "rainbow", "Warm to Cool", "Black, Orange and White"]; 
  let selectedColormap = colormaps[0]; // Default selection

  let elementRef1 = null;
  let elementRef2 = null;
  let elementRef3 = null;

  const dispatch = createEventDispatcher()

  // Workaround: We set $viewerIsLoading only after the viewports are initilized, since the viewer loading icon would disappear otherwise
  let isLoading = false;
  let initialized = false;

  onMount(async () => {
    setTimeout(() => {
      isLoading = $viewerIsLoading;
      initialized = true ;  
    }, 1);
   
  }); 

  $: if (initialized) {
    isLoading = $viewerIsLoading;
  }
  
  // This will be triggered when a new image has been loaded to the store or on re-mount
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

  onDestroy(() => {
    if(!$viewerIsLoading && $images.t1){
      saveCurrentWindowLeveling()
      saveCameras()
    } else{
      // Cancels viewerLoading
      $viewerIsLoading = false
    }

  });

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


    // Remove all annotions created by length tool
    const annotations = annotation.state.getAllAnnotations()
    annotations.forEach((a) => {
      if (a.metadata?.toolName === 'Length') {
        annotation.state.removeAnnotation(a.annotationUID);
      }
    });

    // Reset Window leveling
    if($UserSettings["minMaxWindowLeveling"]){
        resetWindowLeveling("minMax")
    } else {
        resetWindowLeveling("dicomTag")
    }

    for(const viewportID of $viewerState.viewportIds){
      const viewport = renderingEngine.getViewport(viewportID)

      // Reset the camera
      viewport.resetCamera();

      // Update the windowleveling
      const voiRange = { 
        lower: $viewerState.currentWindowLeveling[$viewerState.currentlyDisplayedModality].min,
        upper: $viewerState.currentWindowLeveling[$viewerState.currentlyDisplayedModality].max
      };
      viewport.setProperties({ voiRange: voiRange });
      viewport.render();
    }

  }

  async function changeModality(newModality){
    // Save current window leveling in store
    saveCurrentWindowLeveling()
    
    // Save cameras
    saveCameras()

    await loadImages(newModality)

    // Readding segmentation reprasentation, so that it is displayed in front
    removeAllSegmentationRepresentations()
    addSegmentationRepresentations()
  }

  // Saves the current window leveling in the store
  function saveCurrentWindowLeveling(){

    if($viewerState.currentlyDisplayedModality && $viewerState.renderingEngine){
      try {
        const oldModality = $viewerState.currentlyDisplayedModality

        const renderingEngine = $viewerState.renderingEngine
        const viewport = renderingEngine.getViewport($viewerState.viewportIds[0])

        const currentMax = viewport.getProperties().voiRange.upper
        const currentMin = viewport.getProperties().voiRange.lower

        $viewerState.currentWindowLeveling[oldModality].min = currentMin
        $viewerState.currentWindowLeveling[oldModality].max = currentMax
      } catch (error) {
        console.error("Failed to save window leveling:", error);
      }

    }

  }

  // Save cameras of all viewports in the viewer store, so that it can be used to reset the camera
  function saveCameras(){
    try {
      const renderingEngine = $viewerState.renderingEngine
      for (const [index, viewportID] of $viewerState.viewportIds.entries()) {
        const viewport = renderingEngine.getViewport(viewportID)
        $viewerState.cameras[index] = viewport.getCamera();
      }
    } catch (error) {
      console.error("Failed to save cameras:", error);
    }

  }

  // ================================================================================
  // =============================== Tool Activation functions ======================
  // ================================================================================

  // TODO: Refactor and move to tool.js
  // -> Create one dynamic function: activatePrimaryTool(toolname)

  function activateCrosshairTool(){

    if($viewerState.activePrimaryTool == CrosshairsTool.toolName){
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
    $viewerState.toolGroup.setToolPassive($viewerState.activePrimaryTool);

    $viewerState.activePrimaryTool = CrosshairsTool.toolName
  }

  function activateLengthTool(){

    if($viewerState.activePrimaryTool == LengthTool.toolName){
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
    $viewerState.toolGroup.setToolPassive($viewerState.activePrimaryTool);

    $viewerState.activePrimaryTool = LengthTool.toolName

  }


  function activateEraserTool(){

    if($viewerState.activePrimaryTool == EraserTool.toolName){
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
    $viewerState.toolGroup.setToolPassive($viewerState.activePrimaryTool);

    $viewerState.activePrimaryTool = EraserTool.toolName

  }

  function activateWindowLevelTool(){
    if($viewerState.activePrimaryTool == WindowLevelTool.toolName){
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
    $viewerState.toolGroup.setToolPassive($viewerState.activePrimaryTool);

    $viewerState.activePrimaryTool = WindowLevelTool.toolName
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

      $viewerState.activePrimaryTool = CrosshairsTool.toolName

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

  function rotateArrayRight(arr) {
    if (arr.length === 0) return arr;
    return [arr[arr.length - 1], ...arr.slice(0, arr.length - 1)];
  }

  
  // We don't actually rotate the viewports. Instead we only rotate the orientations in each viewport and apply the right camera
  async function rotateViewports(event) {
    if (event.code === 'Space') {
      event.preventDefault();

      saveCameras()

      // Rotate viewport orientations and cameras
      $viewerState.orientations = rotateArrayRight($viewerState.orientations);
      $viewerState.cameras = rotateArrayRight($viewerState.cameras);
      
      const renderingEngine = $viewerState.renderingEngine
    
      for(const [index, viewportID] of $viewerState.viewportIds.entries()){        
        const viewport = renderingEngine.getViewport(viewportID)
        await viewport.setOrientation($viewerState.orientations[index])  

        setTimeout(async() => {
          await viewport.setCamera($viewerState.cameras[index], false);
          await viewport.render();
        }, 1);


      }

    }
  }


</script>
  
  
<div class="viewer-container"   
  role="button"
  tabindex="0"
  aria-pressed="false"
  on:keydown={rotateViewports}
  >

  <div class="tool-bar">

    <div class="primary-tools">
      <button  
        class="tool {$viewerState.activePrimaryTool === CrosshairsTool.toolName ? 'active' : ''}" 
        on:click={activateCrosshairTool}>
        <CrossHairSymbol/>
      </button>

      <button 
        class="tool {$viewerState.activePrimaryTool === LengthTool.toolName ? 'active' : ''}" 
        on:click={activateLengthTool}>
        <RulerSymbol/>
      </button>

      <button 
        class="tool {$viewerState.activePrimaryTool === EraserTool.toolName ? 'active' : ''}" 
        on:click={activateEraserTool}>
        <EraserSymbol/>
      </button>

      <button 
        class="tool {$viewerState.activePrimaryTool === WindowLevelTool.toolName ? 'active' : ''}" 
        on:click={activateWindowLevelTool}>
        <WindowLevelingSymbol/>
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

      {#if isLoading}
        <div class="loading-container">
          <Loading spinnerSizePx={70}></Loading>
        </div>
      {/if}

    </div>


    <!-- Small Viewports -->
    <div 
      bind:this={elementRef2}
      class="viewport2">

      {#if isLoading}
        <div class="loading-container">
          <Loading spinnerSizePx={35}></Loading>
        </div>
      {/if}
    </div>


    <div 
      bind:this={elementRef3}
      class="viewport3">

      {#if isLoading}
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
    <button 
      class="modality-button {$viewerState.currentlyDisplayedModality === 't1' ? 'selected' : ''}" 
      on:click={() => changeModality("t1")}
    >T1</button>
  
    <button 
      class="modality-button {$viewerState.currentlyDisplayedModality === 't1km' ? 'selected' : ''}" 
      on:click={() => changeModality("t1km")}
    >T1km</button>
  
    <button 
      class="modality-button {$viewerState.currentlyDisplayedModality === 't2' ? 'selected' : ''}" 
      on:click={() => changeModality("t2")}
    >T2</button>
  
    <button 
      class="modality-button {$viewerState.currentlyDisplayedModality === 'flair' ? 'selected' : ''}" 
      on:click={() => changeModality("flair")}
    >Flair</button>
  </div>

  <div class="settings-container"> 
    <button class="settings-button" on:click={() => resetViewer()}><ResetViewerIcon/></button>
    <button class="settings-button" on:click={() => dispatch("openInfoModal")} ><InfoIcon/></button>
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
  .modality-button.selected {
    border-color: var(--button-color-preview); /* Maybe change color */
  }

  .settings-button{
    text-align: center;
    cursor: pointer;
  }
  
</style>