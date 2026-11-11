import { useCallback, useEffect, useState } from "react";

import useCurrentUser from "../../../hooks/useCurrentUser";
import recommendationsService from "../../../services/recommendationsService";
import userService from "../../../services/userService";
import { parseApiError } from "../../../utils/apiErrors";

/**
 * Homepage recipe feed.
 *
 * - Signed in with saved preferences -> personalized recipes.
 * - Signed in without preferences, guests, or if the user lookup fails
 *   for any other reason -> general recipes (guests can always browse).
 */
export default function useRecipesForYou() {
    const user = useCurrentUser();
    const [reloadKey, setReloadKey] = useState(0);
    const [result, setResult] = useState({
        key: "",
        recipes: [],
        personalized: false,
        error: null,
    });

    const authenticated = user.status === "authenticated";
    const requestKey = `${user.status}:${reloadKey}`;

    useEffect(() => {
        if (user.status === "loading") return undefined;

        const controller = new AbortController();
        const options = { signal: controller.signal };

        const load = authenticated
            ? Promise.all([
                  userService.getPreferences(options),
                  recommendationsService.getRecipesForUser(options),
              ]).then(([preferences, recipes]) => ({
                  recipes,
                  personalized: preferences.length > 0,
              }))
            : recommendationsService
                  .getGeneralRecipes(options)
                  .then((recipes) => ({ recipes, personalized: false }));

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
                personalized: false,
                error: parseApiError(error).message,
            });
        });

        return () => controller.abort();
    }, [authenticated, requestKey, user.status]);

    const reload = useCallback(() => setReloadKey((key) => key + 1), []);

    return {
        loading: user.status === "loading" || result.key !== requestKey,
        authenticated,
        personalized: result.personalized,
        recipes: result.recipes,
        error: result.error,
        reload,
    };
}
