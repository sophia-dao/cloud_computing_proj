import { useCallback, useEffect, useState } from "react";

import userService from "../services/userService";
import { isAuthError, parseApiError } from "../utils/apiErrors";

/**
 * Who is using the app right now?
 *
 * status:
 *   "loading"        request in flight
 *   "authenticated"  `user` holds { id, email, display_name, profile_image, ... }
 *   "guest"          nobody is signed in (401, or 403 "credentials not provided")
 *   "error"          anything else (server down, no application profile, ...);
 *                    `error` holds { message, status }
 *
 * There is no auth context yet; when real authentication lands this hook
 * can read from it instead of calling /users/me/.
 */
export default function useCurrentUser() {
    const [state, setState] = useState({
        status: "loading",
        user: null,
        error: null,
    });
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();

        userService
            .getCurrentUser({ signal: controller.signal })
            .then((user) => {
                if (controller.signal.aborted) return;

                setState({ status: "authenticated", user, error: null });
            })
            .catch((error) => {
                if (controller.signal.aborted || error?.name === "AbortError") {
                    return;
                }

                if (isAuthError(error)) {
                    setState({ status: "guest", user: null, error: null });
                } else {
                    setState({
                        status: "error",
                        user: null,
                        error: parseApiError(error),
                    });
                }
            });

        return () => controller.abort();
    }, [reloadKey]);

    const reload = useCallback(() => {
        setState({ status: "loading", user: null, error: null });
        setReloadKey((key) => key + 1);
    }, []);

    return { ...state, reload };
}
