<template>
  <div style="display: flex; justify-content: center; align-items: center; ">
    <div style="width: 800px">

      <!--Papaya-->
      <div id="papaya_viewer" class="papaya" ref="papayaViewer"></div>
      
      <form style="margin: 10px" @submit.prevent="updateImage">
        
        <h3>Upload file:</h3>
        <input type="file" required @change="selectFile">
  
        <button>
          Visualize image
        </button>
      </form>
    
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedFile: null,
      params: { kioskMode: false },
    };
  },
  mounted() {
    window.papaya.Container.startPapaya();
    window.papaya.Container.resetViewer(0, this.params);
  },
  methods: {
    updateImage() {
      if (!this.selectedFile) return;

      try {
        const selectedFileURL = URL.createObjectURL(this.selectedFile);
        this.params.images = [selectedFileURL];
        window.papaya.Container.resetViewer(0, this.params);
      } catch (error) {
        console.error(error);
      }
    },
    selectFile(event) {
      this.selectedFile = event.target.files[0];
    },
  }
};
</script>

<style>
/* Add your CSS styles here */
</style>
