<script>
    import Loading from "../../single-components/Loading.svelte";
    import PageWrapper from "../../single-components/PageWrapper.svelte";
    import { getSettingsAPI, updateSettingsAPI } from "../../lib/api.js";
    import { UserSettings } from "../../stores/Store.js";
    import { onMount, onDestroy } from 'svelte';
    import Modal from "../../shared-components/general/Modal.svelte";
    import { resetWindowLeveling } from "../../stores/ViewerStore";

    let loadingSettings = true;
    let loadingError = false;
    let successfullyLoaded = false;
    let loadedWithError = false;
    let showUpdateSettingsErrorModal = false;
    let showUpdateSettingsSuccessfulModal = false;
    let settingsChanged = false;

    let confirmDeleteSetting = true;
    let numberOfShownSegmentations = "1000000";
    let defaultDownloadType = "nifti";
    let minMaxWindowLeveling = false;

    onMount(async () => {
        try {
            const response = await getSettingsAPI();
            if (response.ok) {
                const data = await response.json();
                $UserSettings = data;
                confirmDeleteSetting = $UserSettings.confirmDeleteEntry;
                numberOfShownSegmentations = "" + $UserSettings.numberDisplayedRecentSegmentations;
                defaultDownloadType = "" + $UserSettings.defaultDownloadType;
                minMaxWindowLeveling = $UserSettings.minMaxWindowLeveling;
                loadingSettings = false;
            } else {
                throw new Error("Response from settings API not ok");
            }
        } catch(error) {
            console.log(error);
            loadingSettings = false;
            loadingError = true;
        }
        setTimeout(() => settingsChanged = false, 100);
    });

    onDestroy(() => {
        if (typeof(window) !== "undefined") {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        }
    });

    function handleBeforeUnload(e) {
        e.preventDefault();
        e.returnValue = "";
    }

    $: {
        successfullyLoaded = !loadingSettings && !loadingError;
        loadedWithError = !loadingSettings && loadingError;
    }

    $: confirmDeleteSetting, settingsChanged = true;
    $: numberOfShownSegmentations, settingsChanged = true;
    $: defaultDownloadType, settingsChanged = true;
    $: minMaxWindowLeveling, settingsChanged = true;

    $: {
        if (typeof(window) !== "undefined") {
            if (settingsChanged) {
                window.addEventListener('beforeunload', handleBeforeUnload);
            } else {
                window.removeEventListener('beforeunload', handleBeforeUnload);
            }
        }
    }

    async function updateSettings() {
        try {
            const curSettings = {
                confirmDeleteEntry: confirmDeleteSetting,
                numberDisplayedRecentSegmentations: numberOfShownSegmentations,
                defaultDownloadType: defaultDownloadType,
                minMaxWindowLeveling: minMaxWindowLeveling
            };

            const response = await updateSettingsAPI(JSON.stringify(curSettings));

            if (response.ok) {
                showUpdateSettingsSuccessfulModal = true;
                if(minMaxWindowLeveling !== $UserSettings.minMaxWindowLeveling){
                    if(minMaxWindowLeveling){
                        resetWindowLeveling("minMax");
                    } else {
                        resetWindowLeveling("dicomTag");
                    }
                }
                settingsChanged = false;
            } else {
                throw new Error("Updating settings failed!");
            }
        } catch(error) {
            console.log(error);
            showUpdateSettingsErrorModal = true;
        }
    }
</script>

<PageWrapper loadSettings={false} bind:hasUnsavedChanges={settingsChanged}>
    <h1 class="page-title">Einstellungen</h1>

    {#if loadingSettings}
        <div class="loading-container">
            <Loading spinnerSizePx={40} />
        </div>
    {:else if successfullyLoaded}
        <p class="intro-text">
            Hier können Sie Ihr Konto und die Darstellung der Webseite individuell anpassen:
        </p>

        <div class="settings-grid">
            <div class="card">
                <h2 class="card-title">Allgemein</h2>
                <div class="setting-row">
                    <label for="no-more-delete-modals">Löschen einzelner Einträge durch ein Popup bestätigen</label>
                    <input type="checkbox" id="no-more-delete-modals" bind:checked={confirmDeleteSetting} class="toggle" />
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">Segmentierungen</h2>
                <div class="setting-row">
                    <label for="num-shown-segmentations">Anzahl angezeigter letzter Segmentierungen</label>
                    <select id="num-shown-segmentations" bind:value={numberOfShownSegmentations}>
                        <option value="5">5</option>
                        <option value="10">10</option>
                        <option value="20">20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                        <option value="1000000">Alle</option>
                    </select>
                </div>
                <div class="setting-row">
                    <label for="default-download">Herunterladen als</label>
                    <select id="default-download" bind:value={defaultDownloadType}>
                        <option value="nifti">Nifti</option>
                        <option value="dicom">Dicom</option>
                    </select>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">Bilddarstellung</h2>
                <div class="setting-row">
                    <label for="min-max-window-leveling">Window Leveling automatisch anpassen</label>
                    <input type="checkbox" id="min-max-window-leveling" bind:checked={minMaxWindowLeveling} class="toggle" />
                    <small class="description">
                        Basierend auf minimalen und maximalen Pixelwerten statt DICOM-Tags.
                    </small>
                </div>
            </div>
        </div>

        <div class="action-buttons">
            <button class="button save-button" on:click={updateSettings}>
                Einstellungen speichern
            </button>
        </div>

    {:else if loadedWithError}
        <div class="error-message">
            Die Einstellungen konnten nicht geladen werden. Bitte später erneut versuchen.
        </div>
    {/if}
</PageWrapper>

<Modal bind:showModal={showUpdateSettingsSuccessfulModal} cancelButtonText="OK" cancelButtonClass="confirm-button">
    <h2 slot="header">Erfolg</h2>
    <p>Die Einstellungen wurden erfolgreich gespeichert.</p>
</Modal>

<Modal bind:showModal={showUpdateSettingsErrorModal} cancelButtonText="OK" cancelButtonClass="main-button">
    <h2 slot="header">Fehler</h2>
    <p>Beim Speichern der Einstellungen ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.</p>
</Modal>

<style>
    .page-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .intro-text {
        margin-bottom: 2rem;
        color: #aaa;
    }
    .settings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
    }
    .card {
        background: #1f2937;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .card-title {
        font-size: 1.2rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .setting-row {
        display: flex;
        flex-direction: column;
        margin-bottom: 1.5rem;
    }
    label {
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    select {
        height: 35px;
        background-color: #111827;
        color: white;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 0 0.75rem;
    }
    .toggle {
        width: 40px;
        height: 20px;
        background: #374151;
        border-radius: 9999px;
        position: relative;
        appearance: none;
        cursor: pointer;
    }
    .toggle:checked {
        background: #3b82f6;
    }
    .toggle:checked::before {
        transform: translateX(20px);
    }
    .toggle::before {
        content: '';
        position: absolute;
        top: 2px;
        left: 2px;
        width: 16px;
        height: 16px;
        background: white;
        border-radius: 9999px;
        transition: 0.3s;
    }
    .description {
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.5rem;
    }
    .action-buttons {
        margin-top: 2rem;
        text-align: right;
    }
    .save-button {
        background: #3b82f6;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .save-button:hover {
        background: #2563eb;
        color: white;
    }
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 200px;
    }
    .error-message {
        color: #f87171;
        font-weight: bold;
        text-align: center;
        margin-top: 2rem;
    }
</style>