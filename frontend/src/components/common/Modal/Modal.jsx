
import { useEffect, useId, useRef } from "react";
import "./Modal.css";

function Modal({
    open = false,
    onClose,
    title,
    description,
    children,
    footer,
    size = "md",
    closeOnBackdrop = true,
    showCloseButton = true,
    className = "",
}) {
    const dialogRef = useRef(null);
    const titleId = useId();
    const descriptionId = useId();

    // Synchronize React state with the native dialog.
    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;

        if (open && !dialog.open) {
            dialog.showModal();
        } else if (!open && dialog.open) {
            dialog.close();
        }
    }, [open]);

    function handleClose() {
        onClose?.();
    }

    function handleCancel(event) {
        // React controls the open state.
        event.preventDefault();
        onClose?.();
    }

    function handleBackdropClick(event) {
        if (
            closeOnBackdrop &&
            event.target === dialogRef.current
        ) {
            onClose?.();
        }
    }

    return (
        <dialog
            ref={dialogRef}
            className={[
                "ui-modal",
                `ui-modal--${size}`,
                className,
            ].filter(Boolean).join(" ")}
            aria-labelledby={title ? titleId : undefined}
            aria-describedby={
                description ? descriptionId : undefined
            }
            aria-label={title ? undefined : "Dialog"}
            onClose={handleClose}
            onCancel={handleCancel}
            onClick={handleBackdropClick}
        >
            <div className="ui-modal__panel">
                {(title || showCloseButton) && (
                    <div className="ui-modal__header">
                        {title && (
                            <h2 id={titleId}>{title}</h2>
                        )}

                        {showCloseButton && (
                            <button
                                type="button"
                                className="ui-modal__close"
                                aria-label="Close dialog"
                                onClick={() => onClose?.()}
                            >
                                &times;
                            </button>
                        )}
                    </div>
                )}

                <div className="ui-modal__body">
                    {description && (
                        <p
                            id={descriptionId}
                            className="ui-modal__description"
                        >
                            {description}
                        </p>
                    )}

                    {children}
                </div>

                {footer && (
                    <div className="ui-modal__footer">
                        {footer}
                    </div>
                )}
            </div>
        </dialog>
    );
}

export default Modal;
