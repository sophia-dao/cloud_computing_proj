
import "./Button.css";

function Button({
    children,
    variant = "primary",
    size = "md",
    type = "button",
    disabled = false,
    loading = false,
    className = "",
    ...props
}) {
    const classes = [
        "ui-button",
        `ui-button--${variant}`,
        `ui-button--${size}`,
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <button
            type={type}
            className={classes}
            disabled={disabled || loading}
            aria-busy={loading}
            {...props}
        >
            {loading ? "Loading..." : children}
        </button>
    );
}

export default Button;
