<script>
    import PageWrapper from "../single-components/PageWrapper.svelte";
    import { createEventDispatcher } from 'svelte';

    let user_mail = '';
    let password = '';
    let error = '';

    // dispatcher to notify main page
    const dispatcher = createEventDispatcher();

    async function handleAccountCreation() {
        try {
            const response = await fetch('http://localhost:5001/brainns-api/auth/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_mail, password }),
                mode: 'cors',
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                // set session_token
                sessionStorage.setItem("session_token", data.session_token);
                // notify mainpage the sucessful login
                dispatcher('accountCreated');
            } else {
                const data = await response.json();
                console.error('Fehler bei der Kontoerstellung: ', data.message);
                error = data.message;
            }
        } catch (err) {
            console.error('Fehler bei der Kontoerstellung:', err);
            error = 'Fehler bei der Kontoerstellung: ' + err.message;
        }
    }
</script>

<PageWrapper>
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
</PageWrapper>

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
