<script>
    import { createEventDispatcher } from 'svelte';
    import { accountCreationAPI } from "../lib/api";

    let user_mail = '';
    let password = '';
    let error = '';

    // dispatcher to notify main page
    const dispatcher = createEventDispatcher();

    async function handleAccountCreation() {
        try {
            let account_creation_result = await accountCreationAPI(user_mail, password)
        
            if (account_creation_result.error === null) {
                // set session_token
                sessionStorage.setItem("session_token", account_creation_result.session_token);
                // notify mainpage the sucessful login
                dispatcher('accountCreated');
            } else {
                console.error('Fehler beim Login: ', account_creation_result.error);
                error = account_creation_result.error;
            }
        } catch (err) {
            console.error('Fehler bei der Kontoerstellung:', err);
            error = 'Fehler bei der Kontoerstellung: ' + err.message;
        }
    }
</script>

<div class="card-container">
    <div class="card">
        <div>
            <h1 class="header">Account erstellen</h1>
            <p id="description">
                Erstellen Sie hier einen neuen Account. Es sind lediglich E-Mail Adressen der Universität zu Lübeck sowie der UKSH zugelassen.
                Zusätzlich müssen die E-Mail Adressen durch den Administrator freigeschaltet werden. 
            </p>
        </div>
        <form on:submit|preventDefault={handleAccountCreation}>
            <input type="text" bind:value={user_mail} placeholder="Email" required />
            <input type="password" bind:value={password} placeholder="Passwort" required />
            <button type="submit" class="login-button">Account anlegen</button>
            {#if error}
                <p class="error">{error}</p>
            {/if}
            <!-- Button zum Wechseln zur Account-Erstellung -->
            <div class="back-arrow" on:click={() => dispatcher('toggleAccountCreation')}>
                ← Zurück zum Login
            </div>
        </form>
    </div>
</div>


<style>
    .back-arrow {
        cursor: pointer;
        color: var(--button-text-color-secondary);
        font-weight: 500;
        text-align: left;
        margin-top: 10px;
        transition: color 0.2s ease;
    }

    .back-arrow:hover {
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
        margin-top: 20px;
        margin-left: 0;
        margin-right: 0;
    }

    p.error {
        color: var(--button-color-error);
    }
</style>
