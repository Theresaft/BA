<script>
    export let inputContent
    export let nameDescription
    let errorText = ""

    /**
     * Validate if the project name entered at the beginning is valid.
     * If false is returned, the name is invalid, otherwise, it's valid.
     **/
	// TODO Refactor this function because this is almost the same as the variant for the segmentation name.
	export function validateName() {
		errorText = ""        

        const forbiddenSymbols = [" ", "/", "\\", ":", "*", "?", "\"", "<", ">", "|", "`"]

        if (inputContent === "") {
            errorText = `Der ${nameDescription} darf nicht leer sein.`
            return false
        }
        // Ensure that none of the forbidden symbols are included in the project title name.
        else if (forbiddenSymbols.find(symbol => inputContent.includes(symbol)) ) {
            errorText = `Der ${nameDescription} darf keins der folgenden Zeichen enthalten: ${formatList(forbiddenSymbols)}`
            return false
        }
        else {
            return true
        }
	}

    // TODO Refactor this
    function formatList(list) {
		// Handle the case where the array is empty
		if (list.length === 0) {
			return "";
		}
		
		// Handle the case where the array has only one item
		if (list.length === 1) {
			return list[0];
		}

        list = list.map(el => el === " " ? "Leerzeichen" : el)
		
		// Get all items except the last one
		const allExceptLast = list.slice(0, -1).join(', ');
		// Get the last item
		const lastItem = list[list.length - 1];
		
		// Combine all items with 'und' before the last one
		return `${allExceptLast} und ${lastItem}`;
	}
</script>

<div class="container">
    <h3 class="description">{nameDescription}:</h3>
    <input type="text" placeholder={nameDescription} class="segmentation-input" bind:value={inputContent}>
    <p class="error-text">{errorText}</p>
</div>

<style>
    .container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 68.72px;
    }
    .description {
        width: 60%;
        text-align: center;
    }
    .segmentation-input {
        width: 40%;
        text-align: left;
        margin-top: 15px;
        font-size: 14px;
        padding: 6px 10px;
        border-radius: 2px;
    }
    .error-text {
        font-size: 15px;
        color: var(--button-color-error);
        /* text-shadow: white 0 0 3px; */
        width: 40%;
        padding: 6px 0;
        text-align: center;
        font-weight: 600;
    }
</style>