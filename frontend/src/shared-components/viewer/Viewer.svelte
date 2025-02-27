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
  import ClassLabel from './ClassLabel.svelte';
  
    // ================================================================================
    // ================================= Variables ====================================
    // ================================================================================
  
    const classLabels = [
      {
        "segmentIndex" : 1,
        "labelName" : "Necrotic Core"
      },
      {
        "segmentIndex" : 2,
        "labelName" : "Enhancing Tumor"
      },
      {
        "segmentIndex" : 3,
        "labelName" : "Edema"
      }
    ]
  
    let elementRef1 = null;
    let elementRef2 = null;
    let elementRef3 = null;
  
  
    $: {
        if ($images.t1) {
          (async () => {
              await loadImages(null, "backend");
              addActiveSegmentation();
          })();

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
      
      $viewerAlreadySetup = true
    }
  
    // Run setup on mount
    onMount(() => {
      setup();
    });
  
  
  </script>
  
  
<div class="viewer-container">

  <div class="viewer"> 
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
      {#each classLabels as classLabel}
        <ClassLabel classLabel={classLabel} />
      {/each}
    </div>
    <div class="tools-container">
      <div class="tool">B</div>
      <div class="tool">R</div>
      <div class="tool">R</div>
      <div class="tool">C</div>
    </div>
  </div>

  <div class="sidebar">    
    <button class="modality-button" on:click={() => loadImages(null, "backend", "t1")}>T1</button>
    <button class="modality-button" on:click={() => loadImages(null, "backend", "t1km")}>T1km</button>
    <button class="modality-button" on:click={() => loadImages(null, "backend", "t2")}>T2</button>
    <button class="modality-button" on:click={() => loadImages(null, "backend", "flair")}>Flair</button>
  </div>

  <div class="settings-container"> 
    <div class="settings-button">A</div>
    <div class="settings-button">B</div>
    <div class="settings-button">C</div>
    <div class="settings-button">D</div>
  </div>

</div>
  
  
      <!-- Sidebar with controlls -->
      <!-- <div class="sidebar">
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
      </div> -->
  
  <style>
    /* General Sidebar Styling */
    button {
      all: unset; /* Resets all inherited/global styles */
    }

    .viewer-container {
      display: grid;
      grid-template-columns: auto 150px;
      grid-template-rows: auto 65px;
      grid-column-gap: 0px;
      grid-row-gap: 0px;
      background-color: black;
      width: 100%;  
      height: 100%; 
      padding: 10px 10px 0px 10px;
      box-sizing: border-box;
    }

    .viewer{ 
      display: grid; 
      grid-area: 1 / 1 / 2 / 2; 
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
      grid-area: 1 / 2 / 2 / 3; 
      display: flex;
      flex-direction: column;
      justify-content: space-evenly;
      align-items: center;
      background-color: black;
    }

    .bottom-bar{
      grid-area: 2 / 1 / 3 / 2; 
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      background-color: black;
    }



    .settings-container {
      grid-area: 2 / 2 / 3 / 3; 
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
    .tools-container{
      display: flex;
      justify-content: space-around;
    }

    .tool{
      margin: 10px;
      padding: 5px 10px;
      background-color: #621631;
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