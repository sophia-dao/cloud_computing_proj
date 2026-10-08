
import { useId } from "react";
import "./Select.css";

function Select({
    label,
    options = [],
    placeholder = "Select an option",
    error,
    helperText,
    id,
    className = "",
    required = false,
    disabled = false,
    ...props
}) {
    const generatedId = useId();
    const selectId = id || generatedId;
    const helperId = `${selectId}-helper`;
    const errorId = `${selectId}-error`;

    const describedBy = [
        error ? errorId : null,
        helperText ? helperId : null,
        props["aria-describedby"],
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div className={`ui-select-field ${className}`}>
            {label && (
                <label
                    className="ui-select-field__label"
                    htmlFor={selectId}
                >
                    {label}

                    {required && (
                        <span
                            className="ui-select-field__required"
                            aria-hidden="true"
                        >
                            {" "}*
                        </span>
                    )}
                </label>
            )}

            <select
                {...props}
                id={selectId}
                required={required}
                disabled={disabled}
                aria-invalid={Boolean(error)}
                aria-describedby={describedBy || undefined}
                className={`ui-select-field__control ${error ? "ui-select-field__control--error" : ""
                    }`}
            >
                <option value="" disabled>
                    {placeholder}
                </option>

                {options.map((option) => (
                    <option
                        key={option.value}
                        value={option.value}
                        disabled={option.disabled || false}
                    >
                        {option.label}
                    </option>
                ))}
            </select>

            {helperText && (
                <span
                    id={helperId}
                    className="ui-select-field__helper"
                >
                    {helperText}
                </span>
            )}

            {error && (
                <span
                    id={errorId}
                    className="ui-select-field__error"
                    role="alert"
                >
                    {error}
                </span>
            )}
        </div>
    );
}

export default Select;
