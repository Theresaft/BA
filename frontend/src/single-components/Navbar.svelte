<script>
    import NavbarObjects from "../stores/Store.js"
    import SettingsSymbol from "../shared-components/svg/SettingsSymbol.svelte"
    import { NavbarPosition } from "../stores/Store.js"
    import { page } from '$app/stores'
    import { get } from "svelte/store"

</script>

<div class="navbar-wrapper">
    <!-- Left-hand elements -->
    <div class="navbar-left-list">
        {#each $NavbarObjects.filter(el => el.displayPosition === get(NavbarPosition).LEFT) as navbarElement}
            <a role="button" tabindex="-1" class="navbar-element" href={navbarElement.route} 
                class:selected={navbarElement.route === $page.url.pathname && navbarElement.highlightWhenSelected}
                class:image-style={navbarElement.displayImage}
                style={navbarElement.displayImage ? `background: url('src/shared-components/${navbarElement.displayImage}') no-repeat scroll 0px 0px` : ""}>
                
                {navbarElement.displayName}
            </a>
        {/each}
     </div>

    <!-- Center elements-->
    <div class="navbar-center-list">
        {#each $NavbarObjects.filter(el => el.displayPosition === get(NavbarPosition).CENTER) as navbarElement}
            <a role="button" tabindex="-1" class="navbar-element" href={navbarElement.route} 
                class:selected={navbarElement.route === $page.url.pathname && navbarElement.highlightWhenSelected}
                class:image-style={navbarElement.displayImage}
                style={navbarElement.displayImage ? `background: url('src/shared-components/${navbarElement.displayImage}') no-repeat scroll 0px 0px` : ""}>
                
                {navbarElement.displayName}
            </a>
        {/each}
    </div>

    <!-- Right-hand elements -->
     <div class="navbar-right-list">
        {#each $NavbarObjects.filter(el => el.displayPosition === get(NavbarPosition).RIGHT) as navbarElement}
        <a role="button" tabindex="-1" class="navbar-element" href={navbarElement.route} 
            class:selected={navbarElement.route === $page.url.pathname && navbarElement.highlightWhenSelected}
            class:image-style={navbarElement.displayImage}
            style={navbarElement.displayImage ? `background: url('src/shared-components/${navbarElement.displayImage}') no-repeat scroll 0px 0px` : ""}>
            
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
        display: flex;
    }
    .navbar-wrapper div {
    }

    .navbar-left-list {
        /* Reset the margin */
        all: unset;

        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: space-evenly;
        /* padding: 0 25%; */
        flex: 4;
    }

    .navbar-center-list {
        /* Reset the margin */
        all: unset;

        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: space-evenly;
        padding: 0 10%;
        flex: 24;
    }

    .navbar-right-list {
        /* Reset the margin */
        all: unset;
        
        list-style-type: none;
        margin: 0;
        display: flex;
        justify-content: center;
        flex: 1;
    }
    .navbar-element {
        cursor: pointer;
        /* border: 1px solid white; */
        transition: background-color 0.5s ease;
        flex: 1;
        padding: 20px;
        min-width: 50px;
        text-align: center;
    }

    .image-style {
        /* min-width: 100%; */
        /* min-height: 100%; */
        padding: 10px;
        margin: 0;
    }

    a {
        all: unset;
    }
</style>