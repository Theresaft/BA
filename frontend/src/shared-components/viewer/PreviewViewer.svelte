<script>
  import Loading from '../../single-components/Loading.svelte'
  import CrossSymbol from "../svg/CrossSymbol.svelte"
  import { createEventDispatcher } from "svelte"
  import { onMount } from 'svelte';
  import { previewViewerState, previewViewerAlreadySetup} from "../../stores/ViewerStore"
  import {loadPreviewImage} from "./image-loader" 

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

  let viewerIsLoading = false

  // ================================================================================
  // ================================= Variables ====================================
  // ================================================================================

  let elementRef1 = null;
  let elementRef2 = null;
  let elementRef3 = null;


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
      $previewViewerState.renderingEngine = new RenderingEngine($previewViewerState.renderingEngineId);

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
  
    await waitForViewportReady($previewViewerState.renderingEngine, $previewViewerState.viewportIds) 

    loadPreviewImage()

    $previewViewerAlreadySetup = true
  }

  // Run setup on mount
  onMount(() => {
    setup();
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
</script>


<!-- PREVIEW VIEWER -->
<div class="preview-modal-container">
    <div class="preview-modal-window">
        <!-- Toolbar for Viewer -->
        <div class="preview-viewer-toolbar">
            <button on:click={() => {}}>A</button>
            <button on:click={() => {}}>B</button>
            <span><strong>Name:</strong> {name}</span>
            <span><strong>Assigned Type:</strong> {type}</span>
            <button id="preview-close-button" on:click={() => dispatch("closeViewer")}> 
                <CrossSymbol/>
            </button>       
        </div>

        <div class="viewer" role="presentation" on:contextmenu={disableRightClick}> 
            <!-- Main Viewport -->
            <div 
                bind:this={elementRef1}
                class="viewport1">  
        
                {#if viewerIsLoading}
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
            
                    {#if viewerIsLoading}
                    <div class="loading-container">
                        <Loading spinnerSizePx={35}></Loading>
                    </div>
                    {/if}
            
                </div>
            
            
                <div 
                    bind:this={elementRef3}
                    class="viewport3">
            
                    {#if viewerIsLoading}
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
    /** PREVIEW VIEWER Styles*/
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
    }

    .preview-modal-window{
        display: flex;
        flex-direction: column;
        width: 55%; 
        height: 75%;
        margin-top: 4%;
    }

    .preview-viewer-toolbar {
        margin: 0px;
        padding: 0px 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        background-color: #000000;
        border-top-left-radius: 5px; 
        border-top-right-radius: 5px;
    }

    .preview-viewer-toolbar button {
        flex: 0 0 auto;
        background-color: #007bff;
        color: white;
        border: none;
        padding: 8px 16px;
        margin: 5px 5px;
        cursor: pointer;
        border-radius: 7px;
    }
    #preview-close-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 35px;
        height: 35px; 
        border-radius: 50%; 
        background-color: #6c6c6c; /* TODO: CHANGE COLOR */
        padding: 0;
    }

    .preview-viewer-toolbar span {
        flex: 1; 
        font-size: 20px;
        text-align: center;
        padding: 8px 16px;
        margin: 5px 5px; 
    }

    .viewer{ 
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: row;
        box-sizing: border-box;
        border: 1px solid white;
        border-radius: 3px;
        width: 100%;
        height: 100%;
        padding: 0px;
        border-bottom-left-radius: 5px; 
        border-bottom-right-radius: 5px;
    }

    .viewport1{
        flex: 1;
        width: 65%;
        height: 100%;
        background-color: lightgrey; 
        border: 2px solid white; 
        box-sizing: border-box;
        position: relative;
    }

    .secondary-viewport-container{
        display: flex;
        width: 35%;
        height: 100%;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }

    .viewport2 { 
        flex: 1;
        width: 100%;
        height: 50%;
        background-color: lightgrey; 
        border: 2px solid white;
        box-sizing: border-box;
        position: relative; 
    }

    .viewport3 { 
        flex: 1;
        width: 100%;
        height: 50%;
        background-color: lightgrey; 
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

</style>