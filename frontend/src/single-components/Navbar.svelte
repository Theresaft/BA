<script>
    import NavbarObjects from "../stores/Store.js"
    import { SelectedRoute } from "../stores/Store.js"
    import { navigate } from "svelte-routing"

    const handleNavbarClick = (route) => {
        SelectedRoute.set(route)
        console.log("Going to " + route)
        // navigate(route)
    }
</script>

<div class="navbar-wrapper">
    <div class="navbar-list">
        {#each $NavbarObjects as navbarElement}
            <a role="button" tabindex="-1" class="navbar-element" href={navbarElement.route} class:selected={navbarElement.route === $SelectedRoute}
            on:click={() => handleNavbarClick(navbarElement.route)}>
            {navbarElement.displayName}
            </a>
        {/each}
    </div>
</div>

<style>
    .selected {
        border-bottom: 2px solid var(--font-color-navbar);
    }
    .navbar-element:hover {
        background-color: var(--background-color-navbar-hover);
    }
    .navbar-wrapper {
        width: 100%;
        margin: 0;
        color: var(--font-color-navbar);
        background: var(--background-color-navbar);
        font-size: 18px;
        font-weight: 600;
        text-align: center;
        user-select: none;
    }
    .navbar-list {
        /* Reset the margin */
        all: unset;
        
        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: space-evenly;
        padding: 0 25%;
    }
    .navbar-element {
        cursor: pointer;
        /* border: 1px solid white; */
        transition: background-color 0.5s ease;
        flex: 1;
        padding: 20px 0;
    }
    a {
        all: unset;
    }
</style>