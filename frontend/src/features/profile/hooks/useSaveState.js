import { useCallback, useEffect, useRef, useState } from "react";

import { useToast } from "../../../hooks/useToast";
import { parseApiError } from "../../../utils/apiErrors";

const IDLE = { status: "idle", message: "", fieldErrors: {} };

/**
 * Tracks the saving / error state of one form section.
 * `run(action, successMessage)` executes an async save, shows a toast on
 * success and keeps the error (and any field errors) for inline display.
 */
export default function useSaveState() {
    const { showToast } = useToast();
    const [state, setState] = useState(IDLE);
    const mounted = useRef(false);

    useEffect(() => {
        mounted.current = true;

        return () => {
            mounted.current = false;
        };
    }, []);

    const run = useCallback(
        async (action, successMessage = "Changes saved.") => {
            setState({ status: "saving", message: "", fieldErrors: {} });

            try {
                await action();

                if (mounted.current) setState(IDLE);
                showToast({ type: "success", message: successMessage });
            } catch (error) {
                const { message, fieldErrors } = parseApiError(error);

                if (mounted.current) {
                    setState({ status: "error", message, fieldErrors });
                }
            }
        },
        [showToast]
    );

    const reset = useCallback(() => setState(IDLE), []);

    return {
        status: state.status,
        message: state.message,
        fieldErrors: state.fieldErrors,
        saving: state.status === "saving",
        run,
        reset,
    };
}
