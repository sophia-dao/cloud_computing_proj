
import "./Badge.css";

function Badge({
    children,
    variant = "neutral",
    size = "md",
    removable = false,
    onRemove,
    disabled = false,
    className = "",
}) {
    const classes = [
        "ui-badge",
        `ui-badge--${variant}`,
        `ui-badge--${size}`,
        disabled && "ui-badge--disabled",
        className,
    ].filter(Boolean).join(" ");

    return (
        <span className={classes}>
            <span className="ui-badge__label">
                {children}
            </span>

            {removable && (
                <button
                    type="button"
                    className="ui-badge__remove"
                    onClick={onRemove}
                    disabled={disabled}
                    aria-label={`Remove ${typeof children === "string" ? children : "tag"}`}
                >
                    ×
                </button>
            )}
        </span>
    );
}

export default Badge;
