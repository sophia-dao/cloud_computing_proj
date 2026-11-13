const DEFAULT_MESSAGE = "Something went wrong. Please try again.";
const NON_FIELD_KEYS = new Set(["detail", "message", "error", "code"]);

function joinMessages(value) {
    if (Array.isArray(value)) return value.map(String).join(" ");
    if (typeof value === "string") return value;
    return "";
}

/**
 * True when the request failed because nobody is signed in.
 *
 * DRF answers 401 when an authenticator provides a challenge header and
 * 403 ("Authentication credentials were not provided.") when it does not,
 * which is what the current session-based default does.
 */
export function isAuthError(error) {
    if (error?.status === 401) return true;

    return (
        error?.status === 403 &&
        typeof error?.data?.detail === "string" &&
        /credentials were not provided/i.test(error.data.detail)
    );
}

/**
 * Normalises an ApiError (see apiClient.js) into
 * { message, status, authRequired, fieldErrors } for display.
 *
 * Handles DRF's default shape ({ field: ["msg"] }) and the documented
 * envelope ({ error: { message, details: { field: [...] } } }).
 */
export function parseApiError(error) {
    const status = error?.status ?? null;
    const data = error?.data;
    const fieldErrors = {};

    let message = error?.message || DEFAULT_MESSAGE;

    if (data && typeof data === "object") {
        if (typeof data.error?.message === "string") {
            message = data.error.message;
        }

        const details = data.error?.details ?? data;

        if (details && typeof details === "object" && !Array.isArray(details)) {
            for (const [key, value] of Object.entries(details)) {
                if (NON_FIELD_KEYS.has(key)) continue;

                const text = joinMessages(value);
                if (text) fieldErrors[key] = text;
            }
        }
    }

    const authRequired = isAuthError(error);

    if (authRequired) {
        message = "Please sign in to manage your profile.";
    } else if (
        status === 400 &&
        Object.keys(fieldErrors).length > 0 &&
        message.startsWith("API request failed")
    ) {
        message = "Some fields are invalid. Please review and try again.";
    }

    return { message, status, authRequired, fieldErrors };
}
