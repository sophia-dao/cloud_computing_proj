
import "./EmptyState.css";

function EmptyState({
    title = "Nothing here yet",
    description = "There is no content to display.",
    icon = "📭",
    action,
    className = "",
}) {
    return (
        <div
            className={[
                "ui-empty-state",
                className,
            ].filter(Boolean).join(" ")}
        >
            {icon && (
                <span className="ui-empty-state__icon" aria-hidden="true">
                    {icon}
                </span>
            )}

            <h3 className="ui-empty-state__title">{title}</h3>

            {description && (
                <p className="ui-empty-state__description">
                    {description}
                </p>
            )}

            {action && (
                <div className="ui-empty-state__action">
                    {action}
                </div>
            )}
        </div>
    );
}

export default EmptyState;
