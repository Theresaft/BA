<script>
  import { onMount } from 'svelte';

  let selectedFile = null;
  let params = { kioskMode: false };

  function updateImage() {
    if (!selectedFile) return;

    try {
      const selectedFileURL = URL.createObjectURL(selectedFile);
      params.images = [selectedFileURL];
      window.papaya.Container.resetViewer(0, params);
    } catch (error) {
      console.error(error);
    }
  }

  function selectFile(event) {
    selectedFile = event.target.files[0];
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
      <input type="file" required on:change={selectFile} />

      <button type="submit">Visualize image</button>
    </form>
  </div>
</div>
