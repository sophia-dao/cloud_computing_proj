
import "./Toast.css";

const icons = {
    success: "✓",
    error: "✕",
    warning: "!",
    info: "i",
};

function Toast({
    type = "info",
    message,
    dismissible = true,
    onClose,
}) {
    return (
        <div
            className={`ui-toast ui-toast--${type}`}
            role={type === "error" ? "alert" : "status"}
        >
            <span
                className="ui-toast__icon"
                aria-hidden="true"
            >
                {icons[type] ?? icons.info}
            </span>

            <span className="ui-toast__message">
                {message}
            </span>

            {dismissible && (
                <button
                    type="button"
                    className="ui-toast__close"
                    aria-label="Dismiss notification"
                    onClick={onClose}
                >
                    ×
                </button>
            )}
        </div>
    );
}

export default Toast;
