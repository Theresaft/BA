<script>
    export let onClick = () => {}
    export let type = "main"
    export let autoMargin = true
</script>

<button on:click class={type} class:auto-margin={autoMargin}>
    <slot></slot>
</button>

<style>
    button {
		margin: 0 5px;
		transition: all .5s ease;
		padding: .5rem 1rem;
		margin-bottom: 1rem;
		flex: 1;
		border: 1px solid #0001;
		cursor: pointer;
		border-radius: 3px;
		background: var(--button-color-main);
		color: var(--button-text-color-primary);
	}
    .auto-margin {
        margin: auto auto;
    }
    button:hover {
        color: var(--button-text-color-secondary);
        background: var(--button-color-main-hover);
    }
    .main-button {
        background: var(--button-color-main);
    }
    .main-button:hover {
        background: var(--button-color-main-hover);
    }
    .confirm-button {
        background: var(--button-color-confirm);
    }
    .confirm-button:hover {
        background: var(--button-color-confirm-hover);
    }
    .warning-button {
        background: var(--button-color-warning);
    }
    .warning-button:hover {
        background: var(--button-color-warning-hover);
    }
    .error-button {
        background: var(--button-color-error);
    }
    .error-button:hover {
        background: var(--button-color-error-hover);
    }
</style>