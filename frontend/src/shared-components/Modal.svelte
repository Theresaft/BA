<script>
	export let showModal; // boolean
    export let buttonText = "Schließen"
    export let buttonClass = "main-button"

	let dialog; // HTMLDialogElement

	$: if (dialog && showModal) dialog.showModal();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog
	bind:this={dialog}
	on:close={() => (showModal = false)}
	on:click|self={() => dialog.close()}
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div on:click class="content-wrapper">
        <div class="header">
		    <slot name="header" />
        </div>
		<hr />
		<slot />
		<hr />
		<!-- svelte-ignore a11y-autofocus -->
        <div class="button-wrapper">
		    <button autofocus class={buttonClass} on:click={() => dialog.close()}>{buttonText}</button>
        </div>
	</div>
</dialog>

<style>
	dialog {
		max-width: 32em;
		border-radius: 0.2em;
		border: none;
		padding: 20px;
	}
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
	}
	dialog > div {
		padding: 1em;
	}
	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 4, 0.64, 1);
	}
    .button-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .header {
        text-align: center;
        margin: 0;
    }
    button {
        margin-top: 20px;
        width: 40%;
    }
	@keyframes zoom {
		from {
			transform: scale(0.95);
		}
		to {
			transform: scale(1);
		}
	}
	dialog[open]::backdrop {
		animation: fade 0.2s ease-out;
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	button {
		display: block;
	}
</style>