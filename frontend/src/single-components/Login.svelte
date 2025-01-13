<script>
    import { createEventDispatcher } from 'svelte';
    import { loginAPI } from "../lib/api";
    import { Projects, getProjectsFromJSONObject, hasLoadedProjectsFromBackend, startPolling } from "../stores/Store"
    import { getAllProjectsAPI } from "../lib/api"

    let user_mail = '';
    let password = '';
    let error = '';

    // dispatcher to notify main page
    const dispatcher = createEventDispatcher();

    async function handleLogin() {
        let login_result = await loginAPI(user_mail, password)

        if (login_result.error === null) {
            // set session_token
            sessionStorage.setItem("session_token", login_result.session_token);

            // Load Projects
            const loadedProjectData = await getAllProjectsAPI()
            $Projects = getProjectsFromJSONObject(loadedProjectData)
            $hasLoadedProjectsFromBackend = true

            // Start polling for ongoing segmentations
            startPolling()

            // notify mainpage the sucessful login
            dispatcher('loginSuccess');
        } else {
            console.error('Fehler beim Login: ', login_result.error);
            error = login_result.error;
        }
    } 
</script>

<div>
    <h1>Login</h1>
    <p id="description">
        Loggen Sie sich ein, um auf Ihre Projekte zugreifen zu können.
    </p>
</div>
<form on:submit|preventDefault={handleLogin}>
    <input type="email" bind:value={user_mail} placeholder="Email" required />
    <input type="password" bind:value={password} placeholder="Passwort" required />
    <button type="submit" class="login-button">Login</button>
    {#if error}
        <p class="error">{error}</p>
    {/if}
</form>
<!-- Button zum Wechseln zur Account-Erstellung -->
<button on:click={() => dispatcher('toggleAccountCreation')}>Account anlegen</button>

<style>
    form {
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 300px;
        margin: auto;
    }

    input {
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    button {
        font-size: 15px;
        font-weight: 600;
        margin-left: 0;
        margin-right: 0;
        margin-top: 20px;
    }

    #description {
        margin-bottom: 100px;
    }

    p.error {
        color: var(--button-color-error);
    }
</style>
