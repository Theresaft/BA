<script>
	import { createEventDispatcher } from "svelte";

	let dispatch = createEventDispatcher()

	export let showModal; // boolean
	export let cancelButtonText = ""
    export let cancelButtonClass = "main-button"
    
	export let confirmButtonText = ""
    export let confirmButtonClass = "confirm-button"

	let dialog; // HTMLDialogElement

	$: if (dialog && showModal) dialog.showModal();

	const cancelClicked = () => {
		dialog.close()
		dispatch("cancel")
	}

	const confirmClicked = () => {
		dialog.close()
		dispatch("confirm")
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog
	bind:this={dialog}
	on:close={() => (showModal = false)}
	on:click|self={() => dialog.close()}
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div on:click class="content-wrapper">
		<!-- The content of the header is shown at the very top above the first horizontal line to make it prominent. -->
        <div class="header">
		    <slot name="header" />
        </div>

		<!-- The main content is enclosed in two horizontal lines. -->
		<hr />
			<slot />
		<hr />
		
		<!-- The content of the footer goes below the second horizontal line to clearly separate it from the main content. -->
		<div class="footer">
			<slot name="footer" />
		</div>
		
		<!-- svelte-ignore a11y-autofocus -->
        <div class="button-wrapper">
			{#if cancelButtonText !== ""}
		    	<button tabindex="-1" class="button {cancelButtonClass}" on:click={() => cancelClicked()}>{cancelButtonText}</button>
			{/if}
			{#if confirmButtonText !== ""}
		    	<button tabindex="-1" class="button {confirmButtonClass}" on:click={() => confirmClicked()}>{confirmButtonText}</button>
			{/if}
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
        flex-direction: row;
        align-items: center;
		justify-content: center;
		width: 100%;
		gap: 10px;
    }
    .header {
        text-align: center;
        margin: 0;
    }
    button {
        margin-top: 20px;
        width: 20%;
		transition: none;
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