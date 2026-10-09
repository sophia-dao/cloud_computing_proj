import { useTheme } from "../../../hooks/useTheme";

import "./ThemeToggle.css";

function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            className="theme-toggle"
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
        >
            {theme === "light" ? "☾" : "☀"}
        </button>
    );
}

export default ThemeToggle;