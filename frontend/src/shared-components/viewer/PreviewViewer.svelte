<script>
  import Loading from '../../single-components/Loading.svelte'
  import CrossSymbol from "../svg/CrossSymbol.svelte"
  import { createEventDispatcher } from "svelte"
  import { onMount, onDestroy } from 'svelte';
  import { previewViewerState, previewViewerAlreadySetup, previewViewerIsLoading, previewImage } from "../../stores/ViewerStore"
  import {loadPreviewImage} from "./image-loader" 
  import ResetViewerIcon from "../svg/ResetViewerIcon.svelte";
  import InfoIcon from "../svg/InfoIcon.svelte";
  import { get } from "svelte/store";

  // Cornerstone CORE
  import {
    init as csRenderInit, 
    RenderingEngine,
    Enums,
  } from '@cornerstonejs/core';
  const { ViewportType } = Enums;
      // Cornerstone TOOLS
      import { init as csToolsInit,
      ToolGroupManager,
      Enums as csToolsEnums,
      StackScrollTool,
      addTool,
      CrosshairsTool,
      ZoomTool,
      PanTool,
      WindowLevelTool,
      synchronizers,
      SynchronizerManager
  } from '@cornerstonejs/tools';
  const { MouseBindings, KeyboardBindings } = csToolsEnums;
  const { createVOISynchronizer } = synchronizers;

  // Dicom Image Loader
  import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader';
  import {getReferenceLineColor, 
      getReferenceLineControllable, 
      getReferenceLineDraggableRotatable, 
      getReferenceLineSlabThicknessControlsOn,
  } from "./previewViewerTool"

  const dispatch = createEventDispatcher()

  export let name = "Name fehlt"
  export let type = "Sequenztyp fehlt"

  // ================================================================================
  // ================================= Variables ====================================
  // ================================================================================

  let elementRef1 = null;
  let elementRef2 = null;
  let elementRef3 = null;

  $: {
        if ($previewImage) {
          // Load image to viewer
          (async () => { 
            if(!get(previewViewerAlreadySetup)) {
              await setup()
            }
            await waitForViewportReady(get(previewViewerState).renderingEngine, get(previewViewerState).viewportIds) 
            await loadPreviewImage();
          })();
        }
      }

  async function setup() {
    
    // Initialization
    await csRenderInit();
    await csToolsInit();

    if(!$previewViewerAlreadySetup){
      dicomImageLoaderInit({ maxWebWorkers: 1 });
    }

    // Add tools to Cornerstone3D
    addTool(StackScrollTool);
    addTool(CrosshairsTool);
    addTool(ZoomTool)
    addTool(PanTool); // Pan Tool = Tool that moves the image
    addTool(WindowLevelTool); 

    if(!$previewViewerAlreadySetup){
      // Define tool groups to add the segmentation display tool to
      $previewViewerState.toolGroup = ToolGroupManager.createToolGroup(
          $previewViewerState.toolGroupId
      );

      /**
       * Configuration of the Tools
      */

      // Stack Scroll Tool
      $previewViewerState.toolGroup.addTool(StackScrollTool.toolName);

      // Zoom Tool
      $previewViewerState.toolGroup.addTool(ZoomTool.toolName);

      // Pan Tool
      $previewViewerState.toolGroup.addTool(PanTool.toolName);

      // Window Level Tool WindowLevelTool
      $previewViewerState.toolGroup.addTool(WindowLevelTool.toolName);


      // Crosshair Tool
      const isMobile = window.matchMedia('(any-pointer:coarse)').matches;
      $previewViewerState.toolGroup.addTool(CrosshairsTool.toolName, {
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

      $previewViewerState.toolGroup.setToolActive(CrosshairsTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Primary }], // Left click
      });  

      $previewViewerState.toolGroup.setToolActive(StackScrollTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Wheel }], // Wheel scroll ;)
      });

      $previewViewerState.toolGroup.setToolActive(ZoomTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Secondary }], // Right click
      });

      $previewViewerState.toolGroup.setToolActive(PanTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Auxiliary }], // Mouse Wheel click
      });

      $previewViewerState.toolGroup.setToolActive(WindowLevelTool.toolName, {
        bindings: [
          {
            mouseButton: MouseBindings.Primary, // Shift Left click
            modifierKey: KeyboardBindings.Shift,
          },
        ], 
      });

      // Instantiate a rendering engine
      if(!$previewViewerState.renderingEngine) {
        $previewViewerState.renderingEngine = new RenderingEngine($previewViewerState.renderingEngineId);
      }

      // Create synchronizers
      createVOISynchronizer($previewViewerState.voiSynchronizerId, {
        syncInvertState: false,
        syncColormap: false,
      });
    }

    // Create the viewports
    const viewportInputArray = [
      {
        viewportId: $previewViewerState.viewportIds[0],
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
        viewportId: $previewViewerState.viewportIds[1],
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
        viewportId: $previewViewerState.viewportIds[2],
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
    
    $previewViewerState.renderingEngine.setViewports(viewportInputArray);
    $previewViewerState.renderingEngine.resize(true);


    $previewViewerState.toolGroup.addViewport($previewViewerState.viewportIds[0], $previewViewerState.renderingEngineId);
    $previewViewerState.toolGroup.addViewport($previewViewerState.viewportIds[1], $previewViewerState.renderingEngineId);
    $previewViewerState.toolGroup.addViewport($previewViewerState.viewportIds[2], $previewViewerState.renderingEngineId);

    // Add viewports to synchronizer
    const synchronizer = SynchronizerManager.getSynchronizer($previewViewerState.voiSynchronizerId);
    const renderingEngineID = $previewViewerState.renderingEngineId

    for(const viewportID of $previewViewerState.viewportIds){
      synchronizer.add({
        renderingEngineId: renderingEngineID,
        viewportId : viewportID
      });
    }

    $previewViewerIsLoading = true

    $previewViewerAlreadySetup = true
  }

  // Run setup on mount
  onMount(() => {
    setup();
    window.addEventListener('keydown', rotateViewports);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', rotateViewports);
  });

  function disableRightClick(event) {
    event.preventDefault();
  }

  function waitForViewportReady(renderingEngine, viewportIds, timeout = 1000) {
    return new Promise((resolve, reject) => {
      const interval = 20;
      const maxTries = timeout / interval;
      let tries = 0;

      const check = () => {
        const allReady = viewportIds.every(id => renderingEngine.getViewport(id));
        if (allReady) {
          resolve();
        } else {
          tries++;
          if (tries > maxTries) reject(new Error("Viewports never became ready"));
          else setTimeout(check, interval);
        }
      };

      check();
    });
  }

  function resetViewer() {
    const renderingEngine = $previewViewerState.renderingEngine

    for(const viewportID of $previewViewerState.viewportIds){
      const viewport = renderingEngine.getViewport(viewportID)

      // Reset the camera
      viewport.resetCamera();

      // // Update the windowleveling
      // const voiRange = { 
      //   lower: $previewViewerState.currentWindowLeveling[$previewViewerState.currentlyDisplayedModality].min,
      //   upper: $previewViewerState.currentWindowLeveling[$previewViewerState.currentlyDisplayedModality].max
      // };
      // viewport.setProperties({ voiRange: voiRange });
      viewport.render();
    }
  }

  // Save cameras of all viewports in the viewer store, so that it can be used to reset the camera
  function saveCameras(){
    try {
      const renderingEngine = $previewViewerState.renderingEngine
      for (const [index, viewportID] of $previewViewerState.viewportIds.entries()) {
        const viewport = renderingEngine.getViewport(viewportID)
        $previewViewerState.cameras[index] = viewport.getCamera();
      }
    } catch (error) {
      console.error("Failed to save cameras:", error);
    }

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
      $previewViewerState.orientations = rotateArrayRight($previewViewerState.orientations);
      $previewViewerState.cameras = rotateArrayRight($previewViewerState.cameras);

      const renderingEngine = $previewViewerState.renderingEngine
    
      for(const [index, viewportID] of $previewViewerState.viewportIds.entries()){        
        const viewport = renderingEngine.getViewport(viewportID)
        await viewport.setOrientation($previewViewerState.orientations[index])  

        setTimeout(async() => {
          await viewport.setCamera($previewViewerState.cameras[index], false);
          await viewport.render();
        }, 1);
      }
    }
  }
</script>


<!-- PREVIEW VIEWER -->
<div class="preview-modal-container">
    <div class="preview-modal-window">
        <!-- Toolbar for Viewer -->
        <div class="preview-viewer-toolbar">
            <button on:click={() => resetViewer()}><ResetViewerIcon width={25} height={25}/></button>
            <button on:click={() => dispatch("openInfoModal")} ><InfoIcon width={29} height={29}/></button>
            <span class="name"><strong>Name:</strong> {name}</span> <!-- shorten -->
            <span class="type"><strong>Assigned Type:</strong> {type}</span> <!-- full -->
            <button id="preview-close-button" on:click={() => dispatch("closeViewer")}>
                <CrossSymbol/>
            </button>
        </div>

        <div class="viewer" role="presentation" on:contextmenu={disableRightClick}> 
            <!-- Main Viewport -->
            <div 
                bind:this={elementRef1}
                class="viewport1">  
        
                {#if $previewViewerIsLoading}
                <div class="loading-container">
                    <Loading spinnerSizePx={70}></Loading>
                </div>
                {/if}
            </div>
        
            <div class="secondary-viewport-container">
                <!-- Small Viewports -->
                <div 
                    bind:this={elementRef2}
                    class="viewport2">
            
                    {#if $previewViewerIsLoading}
                    <div class="loading-container">
                        <Loading spinnerSizePx={35}></Loading>
                    </div>
                    {/if}
            
                </div>
            
            
                <div 
                    bind:this={elementRef3}
                    class="viewport3">
            
                    {#if $previewViewerIsLoading}
                    <div class="loading-container">
                        <Loading spinnerSizePx={35}></Loading>
                    </div>
                    {/if}
            
                </div>
            </div>
        </div>
    </div>
</div>
    

<style>
  /** PREVIEW VIEWER Styles */

  button {
    all: unset; /* Resets all inherited/global styles */
  }

  /* Modal Window for the viewer */
  .preview-modal-container {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      background-color: rgba(0, 0, 0, 0.8); /* dark overlay */
  }

  .preview-modal-window {
      display: flex;
      flex-direction: column;
      width: 70%;
      height: 90%;
      background-color: #1f1f1f; /* dark grey background */
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0px 0px 20px rgba(0,0,0,0.7);
  }

  /* Toolbar */
  .preview-viewer-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: #2b2b2b; /* slightly lighter grey */
      padding: 10px 20px;
      gap: 15px;
  }

  /* Name (more space before truncating) */
  .preview-viewer-toolbar span.name {
      flex: 1 1 auto;
      min-width: 0;
      max-width: 350px; /* More space! */
      font-size: 18px;
      color: white;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
  }

  /* Assigned Type (no truncation) */
  .preview-viewer-toolbar span.type {
      flex: 1 1 auto;
      font-size: 18px;
      color: white;
      text-align: center;
      white-space: normal;
      overflow: visible;
  }

  /* Toolbar Buttons */
  .preview-viewer-toolbar button {
      flex: 0 0 auto;
      color: white;
      border: none;
      margin: 5px 5px 0px 5px;
      cursor: pointer;
      border-radius: 7px;
      transition: background-color 0.2s ease;
  }

  /* Close Button Special */
  #preview-close-button {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 35px;
      height: 35px;
      border-radius: 50%;
      background-color: #6c6c6c;
      padding: 0;
      transition: background-color 0.2s ease;
  }

  #preview-close-button:hover {
      background-color: #555;
  }

  /* Viewer Area */
  .viewer {
      display: flex;
      flex: 1;
      align-items: center;
      justify-content: center;
      flex-direction: row;
      box-sizing: border-box;
      background-color: #1f1f1f; /* match modal background */
      width: 100%;
      height: 100%;
      padding: 0;
  }

  /* Main big viewport */
  .viewport1 {
      flex: 1;
      width: 65%;
      height: 100%;
      background-color: #2e2e2e;
      border: 2px solid #3a3a3a; /* dark grey borders */
      box-sizing: border-box;
      position: relative;
  }

  /* Small secondary viewports container */
  .secondary-viewport-container {
      display: flex;
      width: 35%;
      height: 100%;
      align-items: center;
      justify-content: center;
      flex-direction: column;
  }

  /* Small viewports */
  .viewport2,
  .viewport3 {
      flex: 1;
      width: 100%;
      height: 50%;
      background-color: #2e2e2e;
      border: 2px solid #3a3a3a; /* dark grey borders */
      box-sizing: border-box;
      position: relative;
  }

  /* Loading Spinner Centered */
  .loading-container {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
  }

  </style>
  