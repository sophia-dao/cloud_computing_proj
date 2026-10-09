
import "./Spinner.css";

function Spinner({
    size = "md",
    label = "Loading...",
    className = "",
}) {
    return (
        <div
            className={[
                "ui-spinner",
                `ui-spinner--${size}`,
                className,
            ].filter(Boolean).join(" ")}
            role="status"
            aria-label={label}
        >
            <span className="ui-spinner__circle" aria-hidden="true" />
            <span className="ui-spinner__sr-only">{label}</span>
        </div>
    );
}

export default Spinner;
