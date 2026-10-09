
import { useId } from "react";
import "./Checkbox.css";

function Checkbox({
    label,
    description,
    error,
    id,
    className = "",
    disabled = false,
    ...props
}) {
    const generatedId = useId();
    const inputId = id || generatedId;
    const descriptionId = `${inputId}-description`;
    const errorId = `${inputId}-error`;

    return (
        <div
            className={[
                "ui-checkbox",
                disabled && "ui-checkbox--disabled",
                className,
            ].filter(Boolean).join(" ")}
        >
            <div className="ui-checkbox__row">
                <input
                    {...props}
                    id={inputId}
                    type="checkbox"
                    disabled={disabled}
                    className="ui-checkbox__input"
                    aria-invalid={error ? true : undefined}
                    aria-describedby={
                        error
                            ? errorId
                            : description
                                ? descriptionId
                                : undefined
                    }
                />

                <div className="ui-checkbox__content">
                    <label
                        htmlFor={inputId}
                        className="ui-checkbox__label"
                    >
                        {label}
                    </label>

                    {description && (
                        <p
                            id={descriptionId}
                            className="ui-checkbox__description"
                        >
                            {description}
                        </p>
                    )}
                </div>
            </div>

            {error && (
                <p
                    id={errorId}
                    className="ui-checkbox__error"
                >
                    {error}
                </p>
            )}
        </div>
    );
}

export default Checkbox;
