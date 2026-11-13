import { useEffect, useState } from "react";

import recipeService from "../../../services/api/recipeService";
import { normalizeRecipeName } from "../recipeForm";

const MIN_NAME_LENGTH = 3;

/**
 * Existing recipes with the same name as `name` (case and extra spaces
 * ignored), checked shortly after the user stops typing.
 *
 * Only a warning: a failed check is ignored and never blocks submitting.
 */
export default function useDuplicateNameCheck(name, { debounce = 500 } = {}) {
    const [result, setResult] = useState({ name: "", matches: [] });

    const normalized = normalizeRecipeName(name);
    const checkable = normalized.length >= MIN_NAME_LENGTH;

    useEffect(() => {
        if (!checkable) return undefined;

        const controller = new AbortController();

        const timer = setTimeout(() => {
            recipeService
                .findRecipesWithSameName(normalized, { signal: controller.signal })
                .then((matches) => {
                    if (!controller.signal.aborted) {
                        setResult({ name: normalized, matches });
                    }
                })
                .catch(() => {});
        }, debounce);

        return () => {
            clearTimeout(timer);
            controller.abort();
        };
    }, [normalized, checkable, debounce]);

    // Never show matches that belong to an earlier version of the name.
    return checkable && result.name === normalized ? result.matches : [];
}
