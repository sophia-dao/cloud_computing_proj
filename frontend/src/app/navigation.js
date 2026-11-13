// `access`: "all" (default), "user" (signed-in only) or "guest" (signed-out only).
export const navigationTabs = [
    {
        label: "Home",
        path: "/",
    },
    {
        label: "Recipes",
        path: "/recipes",
    },
    {
        label: "Add Recipe",
        path: "/add-recipe",
        access: "user",
    },
    {
        label: "Cook",
        path: "/cook",
    },
    {
        label: "Dashboard",
        path: "/dashboard",
        access: "user",
    },
    {
        label: "Login",
        path: "/login",
        access: "guest",
    },
    {
        label: "UI Docs",
        path: "/ui-docs",
    },
];

export function getVisibleTabs(tabs, isAuthenticated) {
    return tabs.filter(({ access = "all" }) =>
        access === "all" ||
        (access === "user" && isAuthenticated) ||
        (access === "guest" && !isAuthenticated)
    );
}
