import { useEffect, useState } from "react";

import { useAuth } from "../../../hooks/useAuth";
import { useToast } from "../../../hooks/useToast";
import recipeService from "../../../services/api/recipeService";
import { isAuthError, parseApiError } from "../../../utils/apiErrors";

/**
 * Whether the signed-in user has saved `recipeId`, and a toggle (Issue #14).
 * Guests get `isAuthenticated: false` and no requests are made.
 */
export default function useSavedRecipe(recipeId) {
    const { isAuthenticated } = useAuth();
    const { showToast } = useToast();

    const [state, setState] = useState({ key: "", savedId: null });
    const [busy, setBusy] = useState(false);

    const key = isAuthenticated && recipeId != null ? String(recipeId) : "";

    useEffect(() => {
        if (!key) return undefined;

        const controller = new AbortController();

        recipeService
            .findSavedRecipe(key, { signal: controller.signal })
            .then((saved) => {
                if (!controller.signal.aborted) {
                    setState({ key, savedId: saved?.id ?? null });
                }
            })
            .catch((error) => {
                // If the check fails, show the button as "not saved". Saving
                // again is harmless because the backend never duplicates.
                if (!controller.signal.aborted && error?.name !== "AbortError") {
                    setState({ key, savedId: null });
                }
            });

        return () => controller.abort();
    }, [key]);

    const loading = Boolean(key) && state.key !== key;
    const saved = state.key === key && state.savedId != null;

    async function toggle() {
        if (!key || loading || busy) return;

        setBusy(true);

        try {
            if (saved) {
                await recipeService.unsaveRecipe(state.savedId);
                setState({ key, savedId: null });
            } else {
                const entry = await recipeService.saveRecipe(Number(key));
                setState({ key, savedId: entry.id });
            }
        } catch (error) {
            if (saved && error?.status === 404) {
                // Already removed (e.g. in another tab).
                setState({ key, savedId: null });
            } else {
                showToast({
                    type: "error",
                    message: `Couldn't update your saved recipes. ${
                        isAuthError(error) ? "Please sign in again." : parseApiError(error).message
                    }`,
                });
            }
        } finally {
            setBusy(false);
        }
    }

    return { isAuthenticated, loading, saved, busy, toggle };
}
