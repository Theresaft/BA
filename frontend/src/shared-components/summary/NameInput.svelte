<script>
    import { InvalidSymbolsInNames, formatAllowedSmyoblList } from "../../stores/Store"
    export let inputContent
    export let nameDescription
    export let disabled = false
    export let errorText = ""

    /**
     * Validate if the project name entered at the beginning is valid.
     * An error describing the problem is returned. If the error text is empty,
     * no error has occurred.
     **/
	export function checkSyntax() {

        const forbiddenSymbols = InvalidSymbolsInNames

        if (inputContent === "") {
            return `Der ${nameDescription} darf nicht leer sein.`
        }
        // Ensure that none of the forbidden symbols are included in the project title name.
        else if (forbiddenSymbols.find(symbol => inputContent.includes(symbol)) ) {
            return `Der ${nameDescription} darf keins der folgenden Zeichen enthalten: ${formatAllowedSmyoblList(forbiddenSymbols)}`
        }
        else {
            return ""
        }
	}
</script>

<div class="container">
    <h3 class="description">{nameDescription}:</h3>
    <input type="text" placeholder={nameDescription} class="segmentation-input" bind:value={inputContent} disabled={disabled}>
    <p class="error-text">{errorText}</p>
</div>

<style>
    .container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
    }
    .description {
        width: 60%;
        text-align: center;
    }
    .segmentation-input {
        width: 40%;
        text-align: left;
        margin-top: 10px;
        font-size: 14px;
        padding: 6px 10px;
        border-radius: 2px;
    }
    .segmentation-input:disabled {
        border: 1px solid grey;
        cursor: not-allowed;
    }
    .error-text {
        font-size: 15px;
        color: var(--button-color-error);
        width: 40%;
        padding: 6px 0;
        text-align: center;
        font-weight: 600;
    }
</style>