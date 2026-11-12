import { useEffect, useState } from "react";

import ingredientService from "../../../services/api/ingredientService";

export const MIN_INGREDIENT_QUERY_LENGTH = 2;

/**
 * Debounced backend ingredient search.
 * - Waits `debounce` ms after the last keystroke before calling the API.
 * - Cancels in-flight requests when the query changes or the component unmounts.
 * - Never requests the full ingredient list (empty/short queries are skipped).
 */
export default function useIngredientSearch(query, { debounce = 300 } = {}) {
    const [state, setState] = useState({
        query: "",
        results: [],
        loading: false,
        error: "",
    });

    const trimmed = String(query ?? "").trim();
    const isSearchable = trimmed.length >= MIN_INGREDIENT_QUERY_LENGTH;

    useEffect(() => {
        if (!isSearchable) return undefined;

        const controller = new AbortController();

        const timer = setTimeout(async () => {
            setState((current) => ({
                ...current,
                query: trimmed,
                loading: true,
                error: "",
            }));

            try {
                const results = await ingredientService.searchIngredients(
                    trimmed,
                    { signal: controller.signal }
                );

                if (!controller.signal.aborted) {
                    setState({
                        query: trimmed,
                        results,
                        loading: false,
                        error: "",
                    });
                }
            } catch (error) {
                if (error?.name === "AbortError" || controller.signal.aborted) {
                    return;
                }

                setState({
                    query: trimmed,
                    results: [],
                    loading: false,
                    error: error?.message || "Unable to search ingredients.",
                });
            }
        }, debounce);

        return () => {
            clearTimeout(timer);
            controller.abort();
        };
    }, [trimmed, isSearchable, debounce]);

    if (!isSearchable) {
        return { results: [], loading: false, error: "", isSearchable, settled: false };
    }

    const settled = state.query === trimmed && !state.loading;

    return {
        // Hide results from an older query while the new one is pending.
        results: state.query === trimmed ? state.results : [],
        loading: state.loading || state.query !== trimmed,
        error: state.query === trimmed ? state.error : "",
        isSearchable,
        settled,
    };
}
