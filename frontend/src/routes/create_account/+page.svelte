<script>
    import PageWrapper from "../../single-components/PageWrapper.svelte";

    let user_mail = '';
    let password = '';
    let error = '';

    async function handleAccountCreation() {
        try {
            const response = await fetch('http://localhost:5001/brainns-api/auth/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({user_mail: user_mail, password: password}),
                mode: 'cors',
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Account erstellt: ", data.message)
                // set boolean login
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
        <h1>Account erstellen</h1>
    </div>
    <form on:submit|preventDefault={handleAccountCreation}>
    <input type="email" bind:value={user_mail} placeholder="Email" required />
    <input type="password" bind:value={password} placeholder="Passwort" required />
    <button type="submit">Account anlegen</button>
    {#if error}
        <p>{error}</p>
    {/if}
</form>
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
        padding: 10px;
        border: none;
        border-radius: 4px;
        background-color: #007bff;
        color: white;
        font-size: 16px;
        cursor: pointer;
    }

    button:hover {
        background-color: #0056b3;
    }

    p {
        color: red;
    }
</style>