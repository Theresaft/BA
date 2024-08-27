<script>
  import PageWrapper from "../single-components/PageWrapper.svelte";
</script>

<div>
  <PageWrapper>
  <h1>Start</h1>
  <div>
    <!-- TODO Screenshots einfügen, wenn die Webseite fertig ist -->
    Diese Webseite ermöglicht es, automatisch MRT-Gehirnscans von einem KI-Modell segmentieren zu lassen. Dazu stehen mehrere Modelle zur Verfügung (siehe unten). Dazu müssen Sie sich zunächst mit einem Google-Konto anmelden, um Ihre Daten hochladen, segmentieren und speichern zu können. Danach haben sie Zugriff auf den Tab "Segmentierung", in dem Sie die DICOM-Daten hochladen können. Hier haben Sie die Möglichkeit, die gewünschten Sequenzen zu inkludieren und unerwünschte herauszufiltern. Falls Sie alle Sequenzen auswählen, wird die Sequenz mit der besten Auflösung gewählt. Nachdem Sie die Eingabe bestätigt haben und das gewünschte Modell ausgewählt haben, wird der Segmentierungs-Algorithmus gestartet. Die Ergebnisse der Segmentierung können sie dann im Tab "Viewer" ansehen.
    <h2>Die Modelle</h2>
    <ul>
      <li><strong>nn-Unet:</strong> Beschreibung nn-Unet</li>
      <li><strong>Eigenes Modell:</strong> Die Studierenden, die an diesem Projekt gearbeitet haben, haben ebenfalls ein eigenes Modell trainiert. Weitere Details folgen...</li>
    </ul>
  </div>
  </PageWrapper>
</div>

<!-- {#if $SelectedRoute === "/"}
<StartPage/>
{:else if $SelectedRoute === "/segmentation"}
<SegmentationPage/>
{:else if $SelectedRoute === "/viewer"}
<ViewerPage/>
{:else if $SelectedRoute === "/info"}
<InfoPage/>
{/if} -->

<style>

</style>
