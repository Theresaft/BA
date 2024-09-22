<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte"
    import { ShowNoDeleteModals } from "../../stores/Store.js"

    let deleteModal = $ShowNoDeleteModals

    // Whenever deleteModal is changed on this page, the Store variable will be updated.
    $: {
        $ShowNoDeleteModals = deleteModal
    }
</script>

<div>
    <PageWrapper>
        <h1>Einstellungen</h1>
        Hier können Sie Einstellungen an Ihrem Konto oder der Darstellung der Webseite vornehmen:

        <!-- Read the possible options from the user account and dynamically create elements for each option -->
        <!-- A form is not necessary here because every change directly affects the Store (or, later, the user database if feasible) -->
        <div id="settings-container">
            <input type="checkbox" id="no-more-delete-modals" name="no-more-delete-modals" bind:checked={deleteModal} tabindex="-1">
            <label class="no-select" for="no-more-delete-modals">
                Löschen einzelner Einträge <em>nicht</em> durch Popup bestätigen 
            </label>
        </div>
    </PageWrapper>
</div>

<style>
    .no-select {
        user-select: none;
    }
    #settings-container {
        padding-top: 50px;
    }
    #no-more-delete-modals {

    }
</style>