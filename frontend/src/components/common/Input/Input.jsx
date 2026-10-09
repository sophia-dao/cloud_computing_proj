
import { useId } from "react";
import "./Input.css";

function Input({
    label,
    error,
    helperText,
    id,
    className = "",
    required = false,
    disabled = false,
    type = "text",
    ...props
}) {
    const generatedId = useId();
    const inputId = id || generatedId;
    const helperId = `${inputId}-helper`;
    const errorId = `${inputId}-error`;

    const describedBy = [
        error ? errorId : null,
        helperText ? helperId : null,
        props["aria-describedby"],
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={`ui-input-field ${className}`}>
            {label && (
                <label className="ui-input-field__label" htmlFor={inputId}>
                    {label}
                    {required && (
                        <span className="ui-input-field__required" aria-hidden="true">
                            {" "}*
                        </span>
                    )}
                </label>
            )}

            <input
                {...props}
                id={inputId}
                type={type}
                required={required}
                disabled={disabled}
                aria-invalid={Boolean(error)}
                aria-describedby={describedBy || undefined}
                className={`ui-input-field__control ${error ? "ui-input-field__control--error" : ""
                    }`}
            />

            {helperText && (
                <span id={helperId} className="ui-input-field__helper">
                    {helperText}
                </span>
            )}

            {error && (
                <span id={errorId} className="ui-input-field__error" role="alert">
                    {error}
                </span>
            )}
        </div>
    );
}

export default Input;
