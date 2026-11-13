import { useId } from "react";

import "../Input/Input.css";
import "./TextArea.css";

/**
 * Multi-line counterpart of Input: same label, helper text, error and
 * required-marker behaviour, and the same look.
 */
function TextArea({
    label,
    error,
    helperText,
    id,
    className = "",
    required = false,
    disabled = false,
    rows = 4,
    ...props
}) {
    const generatedId = useId();
    const textAreaId = id || generatedId;
    const helperId = `${textAreaId}-helper`;
    const errorId = `${textAreaId}-error`;

    const describedBy = [
        error ? errorId : null,
        helperText ? helperId : null,
        props["aria-describedby"],
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={`ui-input-field ui-textarea ${className}`}>
            {label && (
                <label className="ui-input-field__label" htmlFor={textAreaId}>
                    {label}
                    {required && (
                        <span className="ui-input-field__required" aria-hidden="true">
                            {" "}*
                        </span>
                    )}
                </label>
            )}

            <textarea
                {...props}
                id={textAreaId}
                rows={rows}
                required={required}
                disabled={disabled}
                aria-invalid={Boolean(error)}
                aria-describedby={describedBy || undefined}
                className={`ui-input-field__control ui-textarea__control ${
                    error ? "ui-input-field__control--error" : ""
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

export default TextArea;
