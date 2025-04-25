<script>
    import { createEventDispatcher } from 'svelte';
    import { loginAPI, getSettingsAPI, getAllProjectsAPI } from "../lib/api";
    import { Projects, getProjectsFromJSONObject, hasLoadedProjectsFromBackend, startPolling, UserSettings } from "../stores/Store"
    
    let user_mail = '';
    let password = '';
    let error = '';

    // dispatcher to notify main page
    const dispatcher = createEventDispatcher();

    async function handleLogin() {
        try {
            let login_result = await loginAPI(user_mail, password)

            if (login_result.error === null) {
                // set session_token
                sessionStorage.setItem("session_token", login_result.session_token);

                // Load Projects
                const loadedProjectData = await getAllProjectsAPI()
                $Projects = getProjectsFromJSONObject(loadedProjectData)
                $hasLoadedProjectsFromBackend = true

                // Load settings
                const response = await getSettingsAPI()
                if (response.ok) {
                    const data = await response.json()
                    // Update store variable
                    $UserSettings = data
                    console.log(data)
                } else {
                    throw new Error("Response from settings API not ok: " + response)
                }

                // Start polling segmentation status
                startPolling()

                // notify mainpage the sucessful login
                dispatcher('loginSuccess');
            } else {
                console.error('Fehler beim Login: ', login_result.error);
                error = login_result.error;
            }
        }
        catch(error) {
            console.log(error)
        }
    }


    /**
     * Get a printable error message
    */
    function getErrorMessage(error) {
        if (error.includes("NetworkError")) {
            return "Ein Netzwerkfehler ist aufgetreten."
        } else {
            // Default case
            return error
        }
    }

</script>

<div class="card-container">
    <div class="card">
        <div>
            <h1 class="header">Login</h1>
            <p id="description">
                Loggen Sie sich ein, um auf Ihre Projekte zugreifen zu können.
            </p>
        </div>
        <form on:submit|preventDefault={handleLogin}>
            <input type="text" bind:value={user_mail} placeholder="Email" required />
            <input type="password" bind:value={password} placeholder="Passwort" required />
            <button type="submit" class="login-button">Login</button>
            {#if error}
                <p class="error">{getErrorMessage(error)}</p>
            {/if}
        <!-- Back arrow link to account creation -->
            <div class="forward-arrow" on:click={() => dispatcher('toggleAccountCreation')}>
                Noch kein Account? → Account erstellen
            </div>
        </form>
    
    </div>
</div>
<style>

.forward-arrow {
    cursor: pointer;
    font-weight: 500;
    text-align: center;
    align-self: center;
    margin-top: 10px;
    transition: color 0.2s ease;
    color: var(--button-text-color-secondary);
}

.forward-arrow:hover {
    color: #0056b3;
    text-decoration: underline;
}
    .card-container{
        margin-top: 50px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .card{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 1.5rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        gap: 30px;
        max-width: 500px;
    }
    .header{
        text-align: center;
    }
    #description{
        text-align: center;
    }
    form {
        display: flex;
        flex-direction: column;
        gap: 10px;
        width: 100%;
        max-width: 350px;
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

    p.error {
        color: var(--button-color-error);
    }
</style>
