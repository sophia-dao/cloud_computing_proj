
import { useId } from "react";
import "./Switch.css";

function Switch({
    label,
    description,
    id,
    disabled = false,
    className = "",
    ...props
}) {
    const generatedId = useId();
    const inputId = id || generatedId;
    const descriptionId = `${inputId}-description`;

    return (
        <div
            className={[
                "ui-switch",
                disabled && "ui-switch--disabled",
                className,
            ].filter(Boolean).join(" ")}
        >
            <div className="ui-switch__row">
                <div className="ui-switch__content">
                    <label
                        htmlFor={inputId}
                        className="ui-switch__label"
                    >
                        {label}
                    </label>

                    {description && (
                        <p
                            id={descriptionId}
                            className="ui-switch__description"
                        >
                            {description}
                        </p>
                    )}
                </div>

                <input
                    {...props}
                    id={inputId}
                    type="checkbox"
                    role="switch"
                    disabled={disabled}
                    className="ui-switch__input"
                    aria-describedby={
                        description ? descriptionId : undefined
                    }
                />
            </div>
        </div>
    );
}

export default Switch;
