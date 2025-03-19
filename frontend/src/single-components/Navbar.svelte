<script>
    import { isLoggedIn } from "../stores/Store.js"
    import { page } from '$app/stores'
    import { onMount } from 'svelte';
    import { logoutAPI } from "../lib/api.js"
    import { base } from "$app/paths"


    async function handleLogout() {
        let logout_error = await logoutAPI(sessionStorage.getItem('session_token'));

        if (logout_error === null) {
            sessionStorage.removeItem("session_token")
            $isLoggedIn = false
            // refresh page
            window.location.reload();
        } else {
            console.error("Fehler beim Logout:", logout_error);
        }
    }

    onMount(() => {
        // Add a listener for logout on window close
        const onBeforeUnload = () => {
            // logout, if the user is logged in on window close (this causes issues because the window gets unloaded on logout events as well)
            //if ($isLoggedIn)
            //    handleLogout();
        };
        window.addEventListener('beforeunload', onBeforeUnload);
    });
</script>

<div class="navbar-wrapper">
    <!-- Left-hand elements -->
    <div class="navbar-left-list">
        <a role="button" tabindex="-1" class="navbar-element" href={base + "/"}
            class:image-style={"svg/UniLogo.svg"}
            style={`background: url('src/shared-components/svg/UniLogo.svg') no-repeat scroll 0px 0px`}>
        </a>
     </div>

    <!-- Center elements-->
    <div class="navbar-center-list">
        <a role="button" tabindex="-1" class="navbar-element" href={`${base}/`} 
            class:selected={`${base}/` === $page.url.pathname}>
            Home
        </a>
        <a role="button" tabindex="-1" class="navbar-element" href={`${base}/viewer`} 
        class:selected={`${base}/viewer` === $page.url.pathname}>
            Viewer
        </a>
        <a role="button" tabindex="-1" class="navbar-element" href={`${base}/info`} 
        class:selected={`${base}/info` === $page.url.pathname}>
            Info
        </a>
    </div>

    <!-- Right-hand elements -->
     <div class="navbar-right-list">
        <!-- It only makes sense to show the logout button when the user is logged in in the first place. The settings are bound to the account, so that element is only shown during login, as well. -->
        {#if $isLoggedIn}
            <a id="settings-element" role="button" tabindex="-1" class="navbar-element" href={`${base}/settings`} 
                class:selected={`${base}/settings` === $page.url.pathname}
                style={`background: url('src/shared-components/svg/SettingsSymbol.svg') no-repeat scroll 0px 0px`}>
            </a>
            <a id="logout-element" role="button" tabindex="-1" class="navbar-element"
                on:click={handleLogout}>
                Logout
            </a>
        {/if}
     </div>
</div>

<style>
    .selected {
        border-bottom: 2px solid var(--font-color-navbar);
    }
    .navbar-element:hover {
        background-color: var(--background-color-navbar-hover);
    }
    .navbar-wrapper {
        width: 100%;
        margin: 0;
        color: var(--font-color-navbar);
        background: var(--background-color-navbar);
        font-size: 18px;
        font-weight: 600;
        text-align: center;
        user-select: none;
        display: flex;
    }
    .navbar-wrapper div {
    }

    .navbar-left-list {
        /* Reset the margin */
        all: unset;

        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: space-evenly;
        /* padding: 0 25%; */
        flex: 4;
    }

    .navbar-center-list {
        /* Reset the margin */
        all: unset;

        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: space-evenly;
        padding: 0 10%;
        flex: 24;
    }

    .navbar-right-list {
        /* Reset the margin */
        all: unset;
        
        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: center;
        flex: 1;
    }
    .navbar-element {
        cursor: pointer;
        /* border: 1px solid white; */
        transition: background-color 0.5s ease;
        flex: 1;
        padding: 20px;
        min-width: 50px;
        text-align: center;
    }
    #settings-element {
        padding: 20px 10px;
    }
    #logout-element {
        margin-right: 25px; 
    }
    .image-style {
        /* min-width: 100%; */
        /* min-height: 100%; */
        padding: 10px;
        margin: 0;
    }

    a {
        all: unset;
    }
</style>