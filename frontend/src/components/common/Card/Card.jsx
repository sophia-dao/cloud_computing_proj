
import "./Card.css";

function Card({
    title,
    description,
    children,
    footer,
    image,
    imageAlt = "",
    bordered = true,
    floating = false,
    padding = true,
    className = "",
    ...props
}) {
    const classes = [
        "ui-card",
        bordered && "ui-card--bordered",
        floating && "ui-card--floating",
        !padding && "ui-card--no-padding",
        className,
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <article className={classes} {...props}>
            {image && (
                <div className="ui-card__image">
                    <img src={image} alt={imageAlt} />
                </div>
            )}

            <div className="ui-card__body">
                {(title || description) && (
                    <div className="ui-card__header">
                        {title && <h3>{title}</h3>}
                        {description && <p>{description}</p>}
                    </div>
                )}

                {children && (
                    <div className="ui-card__content">
                        {children}
                    </div>
                )}
            </div>

            {footer && (
                <div className="ui-card__footer">
                    {footer}
                </div>
            )}
        </article>
    );
}

export default Card;
