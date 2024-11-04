<script>
    import PageWrapper from "../single-components/PageWrapper.svelte";
    import { createEventDispatcher } from 'svelte';

    let user_mail = '';
    let password = '';
    let error = '';

    // dispatcher to notify main page
    const dispatcher = createEventDispatcher();

    async function handleLogin() {
        try {
            const response = await fetch('http://127.0.0.1:5001/brainns-api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
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
                dispatcher('loginSuccess');
            } else {
                const data = await response.json();
                console.error('Fehler beim Login: ', data.message);
                error = data.message;
            }
        } catch (err) {
            console.error('Fehler beim Login:', err);
            error = 'Fehler beim Login: ' + err.message;
        }
    }
</script>

<PageWrapper>
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
