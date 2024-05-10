<script>
  import { onMount } from 'svelte';

  class MyCtxManager {
    constructor() {
      this.loggedPoints = [];
      this.isDrawing = false;
      this.currentPath = [];

    }

    static menudata = {
      "label": "Test",
      "items": [
        {"label": "Log Point", "action": "Context-Log"},
        {"label": "Clear Points", "action": "Context-Clear"},
        {"label": "Start Drawing", "action": "Context-Drawing"}
      ]
    };

    getContextAtImagePosition(x, y, z) {
      console.log("Say hello");
      return MyCtxManager.menudata;
    }

    actionPerformed(action) {
      if (action === "Log") {
        var currentCoor = papayaContainers[0].viewer.cursorPosition;
        var coor = new papaya.core.Coordinate(currentCoor.x, currentCoor.y, currentCoor.z);
        this.loggedPoints.push(coor);
      } else if (action === "Clear") {
        this.loggedPoints = [];
      } else if (action === "Drawing") {
        // Toggle drawing mode
        this.isDrawing = !this.isDrawing;
        if (!this.isDrawing) {
          // Clear current drawing path
          this.currentPath = [];
        }
      } 

      papayaContainers[0].viewer.drawViewer();
    }

    drawToViewer(ctx) {
      for (var ctr = 0; ctr < this.loggedPoints.length; ctr += 1) {
        if (papayaContainers[0].viewer.intersectsMainSlice(this.loggedPoints[ctr])) {
          var screenCoor = papayaContainers[0].viewer.convertCoordinateToScreen(this.loggedPoints[ctr]);
          ctx.fillStyle = "rgb(255, 0, 0)";
          ctx.fillRect(screenCoor.x, screenCoor.y, 5, 5);

          var originalCoord = papayaContainers[0].viewer.convertScreenToImageCoordinate(screenCoor.x, screenCoor.y);
          var world = new papaya.core.Coordinate();
          papayaContainers[0].viewer.getWorldCoordinateAtIndex(originalCoord.x, originalCoord.y, originalCoord.z, world);
          console.log(originalCoord.toString() + " " + world.toString());
        }
      }
      if (this.isDrawing) {
        // Add coord to path
        var currentCoor = papayaContainers[0].viewer.cursorPosition;
        var coor = new papaya.core.Coordinate(currentCoor.x, currentCoor.y, currentCoor.z);
        this.currentPath.push(coor);

        for (var ctr = 0; ctr < this.currentPath.length; ctr += 1) {
          if (papayaContainers[0].viewer.intersectsMainSlice(this.currentPath[ctr])) {
            var screenCoor = papayaContainers[0].viewer.convertCoordinateToScreen(this.currentPath[ctr]);
            ctx.fillStyle = "rgb(255, 0, 0)";
            ctx.fillRect(screenCoor.x, screenCoor.y, 5, 5);

            var originalCoord = papayaContainers[0].viewer.convertScreenToImageCoordinate(screenCoor.x, screenCoor.y);
            var world = new papaya.core.Coordinate();
            papayaContainers[0].viewer.getWorldCoordinateAtIndex(originalCoord.x, originalCoord.y, originalCoord.z, world);
            console.log(originalCoord.toString() + " " + world.toString());
          }
       }
      }
    }

    clearContext() {
      // do nothing
    }
  }



  let selectedBaseImage = null;
  let selectedMask = null;
  let params = { 
    kioskMode: false ,
    showSurfacePlanes: true, 
    contextManager: new MyCtxManager()
  }
 


  function updateImage() {
    if (!selectedBaseImage) return;

    try {
      const selectedBaseImageURL = URL.createObjectURL(selectedBaseImage);
      const selectedMaskURL = selectedMask ? URL.createObjectURL(selectedMask) : null;
      params.images = [selectedBaseImageURL,selectedMaskURL];
      window.papaya.Container.resetViewer(0, params);
    } catch (error) {
      console.error(error);
    }
  }

  function selectBaseImage(event) {
    selectedBaseImage = event.target.files[0];
  }

  function selectMask(event) {
    selectedMask = event.target.files[0];
  }

  onMount(() => {
    window.papaya.Container.startPapaya();
    window.papaya.Container.resetViewer(0, params);
  });
</script>

<div style="display: flex; justify-content: center; align-items: center;">
  <div style="width: 800px;">
    <!-- Papaya -->
    <div id="papaya_viewer" class="papaya"></div>

    <form style="margin: 10px;" on:submit|preventDefault={updateImage}>
      <h3>Upload file:</h3>
      <label for="base_image">Base Image:</label>
      <input id="base_image" type="file" required on:change={selectBaseImage} />

      <label for="mask">Mask:</label>
      <input id="mask" type="file" on:change={selectMask} />
      

      <button type="submit">Visualize image</button>
    </form>
  </div>
</div>
