<!-- This wrapper is intended to be used by every +page.svelte of the project. The wrapper includes the navbar and footer elements.
 The content inside the page wrapper is arbitrary. It should be noted that the slot content is already contained in a main tag, meaning
 that containing it in such a tag again would be redundant and can lead to erroneous layouts. -->
<script>
    import Navbar from "./Navbar.svelte"
    import Footer from "./Footer.svelte"

    export let removeMainSideMargin = false
</script>

<div>
    <Navbar/>
    <main class:remove-main-side-margin={removeMainSideMargin}>
        <slot>

        </slot>
    </main>
    <Footer/>
</div>

<style>
    main {
        margin-top: var(--margin-main-top);
        margin-left: var(--margin-main-left-right);
        margin-right: var(--margin-main-left-right);
    }
    .remove-main-side-margin {
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
    }
</style>