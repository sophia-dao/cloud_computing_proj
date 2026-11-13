import { useCallback, useEffect, useState } from "react";

import useCurrentUser from "../../../hooks/useCurrentUser";
import recommendationsService from "../../../services/recommendationsService";
import userService from "../../../services/userService";
import { parseApiError } from "../../../utils/apiErrors";

/**
 * Homepage recipe feed. `source` says where the recipes came from:
 *
 * - "ingredients":  signed in, and some recipes use their saved ingredients
 *                   (POST /api/recommendations/).
 * - "preferences":  signed in, nothing matches their ingredients yet (e.g. none
 *                   saved), but they have saved preferences -> recipe list
 *                   filtered by those preferences.
 * - "general":      signed in without either, or a guest -> general recipes
 *                   (guests can always browse).
 */
async function loadForSignedInUser(options) {
    const [preferences, matched] = await Promise.all([
        userService.getPreferences(options),
        recommendationsService.getRecommendationsForUser(options),
    ]);

    if (matched.length > 0) {
        return { recipes: matched, source: "ingredients" };
    }

    const recipes = await recommendationsService.getRecipesForUser(options);

    return {
        recipes,
        source: preferences.length > 0 ? "preferences" : "general",
    };
}

export default function useRecipesForYou() {
    const user = useCurrentUser();
    const [reloadKey, setReloadKey] = useState(0);
    const [result, setResult] = useState({
        key: "",
        recipes: [],
        source: "general",
        error: null,
    });

    const authenticated = user.status === "authenticated";
    const requestKey = `${user.status}:${reloadKey}`;

    useEffect(() => {
        if (user.status === "loading") return undefined;

        const controller = new AbortController();
        const options = { signal: controller.signal };

        const load = authenticated
            ? loadForSignedInUser(options)
            : recommendationsService
                  .getGeneralRecipes(options)
                  .then((recipes) => ({ recipes, source: "general" }));

        load.then((loaded) => {
            if (controller.signal.aborted) return;

            setResult({ key: requestKey, error: null, ...loaded });
        }).catch((error) => {
            if (controller.signal.aborted || error?.name === "AbortError") {
                return;
            }

            setResult({
                key: requestKey,
                recipes: [],
                source: "general",
                error: parseApiError(error).message,
            });
        });

        return () => controller.abort();
    }, [authenticated, requestKey, user.status]);

    const reload = useCallback(() => setReloadKey((key) => key + 1), []);

    return {
        loading: user.status === "loading" || result.key !== requestKey,
        authenticated,
        source: result.source,
        recipes: result.recipes,
        error: result.error,
        reload,
    };
}
