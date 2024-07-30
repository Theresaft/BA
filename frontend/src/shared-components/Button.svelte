<script>
    export let onClick = () => {}
    export let type = "main"
</script>

<button on:click class={type}>
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
    button:hover {
        color: var(--button-text-color-secondary);
        background: var(--button-color-main-hover);
    }
    .main {
        background: var(--button-color-main);
    }
    .main:hover {
        background: var(--button-color-main-hover);
    }
    .confirm {
        background: var(--button-color-confirm);
    }
    .confirm:hover {
        background: var(--button-color-confirm-hover);
    }
    .warning {
        background: var(--button-color-warning);
    }
    .warning:hover {
        background: var(--button-color-warning-hover);
    }
    .error {
        background: var(--button-color-error);
    }
    .error:hover {
        background: var(--button-color-error-hover);
    }
</style>