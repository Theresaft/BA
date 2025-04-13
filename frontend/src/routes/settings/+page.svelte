<script>
    import Loading from "../../single-components/Loading.svelte"
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import { getSettingsAPI, updateSettingsAPI } from "../../lib/api.js"
    import { UserSettings } from "../../stores/Store.js"
    import { onMount, onDestroy } from 'svelte';
    import Modal from "../../shared-components/general/Modal.svelte";

    let loadingSettings = true
    let loadingError = false
    let successfullyLoaded = false
    let loadedWithError = false
    let showUpdateSettingsErrorModal = false
    let showUpdateSettingsSuccessfulModal = false
    let settingsChanged = false

    // ------------ Settings
    // Keep these in sync with the reactive value below that keeps updating the variable settingsChanged
    let confirmDeleteSetting = true
    let numberOfShownSegmentations = "1000000"
    let defaultDownloadType = "nifti"
    let minMaxWindowLeveling = false
    // ------------

    // Get the settings for the user
    onMount(async () => {
        try {
            const response = await getSettingsAPI()
            if (response.ok) {
                const data = await response.json()
                // Update store variable
                $UserSettings = data
                confirmDeleteSetting = $UserSettings.confirmDeleteEntry
                numberOfShownSegmentations = "" + $UserSettings.numberDisplayedRecentSegmentations
                defaultDownloadType = "" + $UserSettings.defaultDownloadType
                minMaxWindowLeveling = $UserSettings.minMaxWindowLeveling

                console.log($UserSettings)
                loadingSettings = false
            } else {
                throw new Error("Response from settings API not ok")
            }
        } catch(error) {
            console.log(error)
            loadingSettings = false
            loadingError = true
        }
        setTimeout(() => {
            settingsChanged = false
        }, 100)
    });

    onDestroy(() => {
        if (typeof(window) != "undefined") {
            window.removeEventListener('beforeunload', handleBeforeUnload)
        }
    })


    function handleBeforeUnload(e) {
        e.preventDefault()
        e.returnValue = ""
    }

    // These are more readable shortcuts for successful loading and loading with an error.
    $: {
        successfullyLoaded = !loadingSettings && !loadingError
        loadedWithError = !loadingSettings && loadingError
    }

    // If any setting is changed, update the settingsChanged variable
    $: confirmDeleteSetting, settingsChanged = true
    $: numberOfShownSegmentations, settingsChanged = true
    $: defaultDownloadType, settingsChanged = true
    $: minMaxWindowLeveling, settingsChanged = true

    // The window event listener is kept in sync with the settingsChanged variable
    $: {
        if (typeof(window) != "undefined") {
            if (settingsChanged) {
                window.addEventListener('beforeunload', handleBeforeUnload)
            } else {
                window.removeEventListener('beforeunload', handleBeforeUnload)
            }
        }
    }


    async function updateSettings() {
        try {
            const curSettings = {
                "confirmDeleteEntry" : confirmDeleteSetting,
                "numberDisplayedRecentSegmentations" : numberOfShownSegmentations,
                "defaultDownloadType" : defaultDownloadType,
                "minMaxWindowLeveling" : minMaxWindowLeveling
            }

            const response = await updateSettingsAPI(JSON.stringify(curSettings))

            if (response.ok) {
                showUpdateSettingsSuccessfulModal = true

                // Since the settings have been saved, it's OK to leave the page now
                settingsChanged = false
            } else {
                throw new Error("Updating settings failed!")
            }

        } catch(error) {
            console.log(error)
            showUpdateSettingsErrorModal = true
        }
    }
</script>

<div>
    <PageWrapper loadSettings={false} bind:hasUnsavedChanges={settingsChanged}>
        <h1>Einstellungen</h1>
        {#if loadingSettings}
            <div class="loading-symbol-container">
                <Loading spinnerSizePx={30}/>
            </div>
        {:else if successfullyLoaded}
            Hier können Sie Einstellungen an Ihrem Konto oder der Darstellung der Webseite vornehmen:
            <!-- Read the possible options from the user account and dynamically create elements for each option -->
            <!-- A form is not necessary here because every change directly affects the Store (or, later, the user database if feasible) -->
            <div id="settings-container">
                <div class="setting">
                    <input type="checkbox" id="no-more-delete-modals" name="no-more-delete-modals" bind:checked={confirmDeleteSetting} tabindex="-1">
                    <label class="no-select" for="no-more-delete-modals">
                        Löschen einzelner Einträge durch Popup bestätigen 
                    </label>
                </div>
                <div class="setting">
                    <label class="no-select" for="num-shown-segmentations">
                        Anzahl angezeigter letzter Segmentierungen in Seitenleiste:
                    </label>
                    <select id="num-shown-segmentations" name="num-shown-segmentations" bind:value={numberOfShownSegmentations}>
                        <option value="5">5</option>
                        <option value="10">10</option>
                        <option value="20">20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                        <option value="1000000">Alle</option>
                    </select>
                </div>
                <div class="setting">
                    <label class="no-select" for="default-download">
                        Segmentierungen herunterladen als:
                    </label>
                    <select id="default-download" name="default-download" bind:value={defaultDownloadType}>
                        <option value="nifti">nifti</option>
                        <option value="dicom">dicom</option>
                    </select>
                </div>
                <div class="setting">
                    <input type="checkbox" id="min-max-window-leveling" name="min-max-window-leveling" bind:checked={minMaxWindowLeveling} tabindex="-1">
                    <label class="no-select" for="min-max-window-leveling">
                        Stelle das Window Leveling basierend auf dem minimalen und maximalen Pixelwert ein. (Das standardmäßige Window Leveling wird anhand der DICOM-Tags festgelegt.)
                    </label>
                </div>
            </div>
            
            <button class="button confirm-button" on:click={updateSettings}>Einstellungen speichern</button>
        {:else if loadedWithError}
            Die Einstellungen konnten nicht geladen werden. Bitte später erneut versuchen.
        {/if}
    </PageWrapper>
</div>

<Modal bind:showModal={showUpdateSettingsSuccessfulModal} cancelButtonText="OK" cancelButtonClass="confirm-button">
    <h2 slot="header">
        Aktualisieren der Einstellungen erfolgreich
    </h2>
    <p>
        Die Einstellungen wurden erfolgreich aktualisiert.
    </p>
</Modal>

<Modal bind:showModal={showUpdateSettingsErrorModal} cancelButtonText="OK" cancelButtonClass="main-button">
    <h2 slot="header">
        Fehler beim Aktualisieren der Einstellungen
    </h2>
    <p>
        Beim Aktualisieren der Einstellungen ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.
    </p>
</Modal>

<style>
    .no-select {
        user-select: none;
    }
    #settings-container {
        padding-top: 50px;
        display: flex;
        flex-direction: column;
        gap: 30px;
        margin-bottom: 40px;
    }
    select {
        text-align: center;
        height: 30px;
        width: 80px;
    }
    .loading-symbol-container {
        width: 100%;
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .setting {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 20px;
    }
    input[type=checkbox] {
        --scale: 1.5;
        -ms-transform: scale(var(--scale)); /* IE */
        -moz-transform: scale(var(--scale)); /* FF */
        -webkit-transform: scale(var(--scale)); /* Safari and Chrome */
        -o-transform: scale(var(--scale)); /* Opera */
        transform: scale(var(--scale));
        align-self: center;
    }
</style>