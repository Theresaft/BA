<script>
    import { onMount } from "svelte";
    import "../app.css"
    import { logoutAPI } from "../lib/api";
    
    // wait for mounting, such that sessionStore is accessable
    onMount(() => {
        // register an event listener for beforeunload
        const handleBeforeUnload = async (event) => {
            console.log("window is closed: logging out...");

            const session_token = sessionStorage.getItem("session_token");
            if (session_token) {
                const error = await logoutAPI(session_token);

                if (error) {
                    console.error("Logout failed:", error);
                } else {
                    console.log("Logout successful");
                    sessionStorage.removeItem("session_token");
                }
            } else {
                console.warn("No session token found for logout");
            }
        };

        window.addEventListener("beforeunload", handleBeforeUnload);

        // cleanup listener on component destroy
        return () => {
            window.removeEventListener("beforeunload", handleBeforeUnload);
        };
    });
</script>

<slot/>