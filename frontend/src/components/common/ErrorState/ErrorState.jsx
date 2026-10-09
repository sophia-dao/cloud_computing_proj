
import Button from "../Button/Button";
import "./ErrorState.css";

function ErrorState({
    title = "Something went wrong",
    description = "We couldn't complete your request. Please try again.",
    onRetry,
    retryLabel = "Try Again",
    className = "",
}) {
    return (
        <div
            className={[
                "ui-error-state",
                className,
            ].filter(Boolean).join(" ")}
            role="alert"
        >
            <div className="ui-error-state__icon" aria-hidden="true">
                !
            </div>

            <h3 className="ui-error-state__title">{title}</h3>

            {description && (
                <p className="ui-error-state__description">
                    {description}
                </p>
            )}

            {onRetry && (
                <Button variant="secondary" onClick={onRetry}>
                    {retryLabel}
                </Button>
            )}
        </div>
    );
}

export default ErrorState;
