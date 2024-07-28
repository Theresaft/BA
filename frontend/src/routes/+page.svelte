<script>
  import Navbar from "../single-components/Navbar.svelte";
  import { SelectedRoute } from "../stores/Store";
  import StartPage from "../single-components/pages/StartPage.svelte";
  import SegmentationPage from "../single-components/pages/SegmentationPage.svelte";
  import ViewerPage from "../single-components/pages/ViewerPage.svelte";
  import InfoPage from "../single-components/pages/InfoPage.svelte";
</script>

<div>
  <Navbar/>
  <!-- This is only a temporary solution for debugging! This should be done with routes. -->
  <main>
    {#if $SelectedRoute === "/"}
      <StartPage/>
    {:else if $SelectedRoute === "/segmentation"}
      <SegmentationPage/>
    {:else if $SelectedRoute === "/viewer"}
      <ViewerPage/>
    {:else if $SelectedRoute === "/info"}
      <InfoPage/>
    {/if}
  </main>
</div>

<style>
  main {
    margin-top: var(--margin-main-top);
    margin-left: var(--margin-main-left-right);
    margin-right: var(--margin-main-left-right);
  }
</style>
