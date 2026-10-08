
import "./FormCard.css";

function FormCard({
    title,
    description,
    children,
    footer,
    columns = 1,
    bordered = true,
    floating = false,
    onSubmit,
    className = "",
    ...props
}) {
    const classes = [
        "ui-form-card",
        bordered && "ui-form-card--bordered",
        floating && "ui-form-card--floating",
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <form
            className={classes}
            onSubmit={onSubmit}
            {...props}
        >
            {(title || description) && (
                <div className="ui-form-card__header">
                    {title && <h2>{title}</h2>}
                    {description && <p>{description}</p>}
                </div>
            )}

            <div
                className="ui-form-card__fields"
                style={{
                    "--form-columns": Math.max(1, Number(columns) || 1),
                }}
            >
                {children}
            </div>

            {footer && (
                <div className="ui-form-card__footer">
                    {footer}
                </div>
            )}
        </form>
    );
}

export default FormCard;
