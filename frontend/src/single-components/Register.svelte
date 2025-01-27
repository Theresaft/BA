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

<div>
    <h1>Account erstellen</h1>
    <p id="description">
        Erstellen Sie hier einen neuen Account. Es sind lediglich E-Mail Adressen der Universität zu Lübeck sowie der UKSH zugelassen.
        Zusätzlich müssen die E-Mail Adressen durch den Administrator freigeschaltet werden. 
    </p>
</div>
<form on:submit|preventDefault={handleAccountCreation}>
    <input type="email" bind:value={user_mail} placeholder="Email" required />
    <input type="password" bind:value={password} placeholder="Passwort" required />
    <button type="submit">Account anlegen</button>
    {#if error}
        <p class="error">{error}</p>
    {/if}
</form>
<!-- Button zum Wechseln zur Account-Erstellung -->
<button on:click={() => dispatcher('toggleAccountCreation')}>Login</button>

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
