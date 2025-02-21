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
    } from '@cornerstonejs/tools';
    const { MouseBindings } = csToolsEnums;
  
    // Dicom Image Loader
    import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader';

    
   import {images, viewerIsLoading} from "../../stores/ViewerStore"

   import {loadImages, loadNiftiImage} from "./image-loader"
   import {addActiveSegmentation} from "./segmentation"
   import {exportSegmentation, importSegmentation} from "./segmentation-export-import"
   import {getReferenceLineColor, 
      getReferenceLineControllable, 
      getReferenceLineDraggableRotatable, 
      getReferenceLineSlabThicknessControlsOn,
      toogleBrush
  } from "./tool"
  
    // ================================================================================
    // ================================= Variables ====================================
    // ================================================================================
  
  
    let elementRef1 = null;
    let elementRef2 = null;
    let elementRef3 = null;
  
  
    $: {
        if ($images.t1) {
          loadImages(null, "backend");
        }
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
            background: [1, 0, 1],
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
            background: [1, 0, 1],
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
            background: [1, 0, 1],
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
        {#if $viewerIsLoading}
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
          <label for="label2" class="control-label">Segmentation:</label>
          <div id="label2" class="control-buttons">
            <button class="btn btn-primary" on:click={() => addActiveSegmentation()}>Create + Load Segmentation</button>
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
        <div class="control-group-2">
          <label for="label3" class="control-label">Base Image (DICOM):</label>
            <button class="btn btn-primary" on:click={() => loadImages(null, "backend", "t1")}>T1</button>
            <button class="btn btn-primary" on:click={() => loadImages(null, "backend", "t1km")}>T1km</button>
            <button class="btn btn-primary" on:click={() => loadImages(null, "backend", "t2")}>T2</button>
            <button class="btn btn-primary" on:click={() => loadImages(null, "backend", "flair")}>Flair</button>
         
        </div>
        <div class="control-group-2">
          <label for="label3" class="control-label">Nifti:</label>
          <button class="btn btn-primary" on:click={() => loadNiftiImage()}>Flair</button>
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
  .control-group-2 {
    display: flex;
    flex-direction: column;
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