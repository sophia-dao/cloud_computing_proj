import { useEffect, useState } from "react";

import Button from "../../../components/common/Button/Button";
import SearchBar from "../../../components/common/SearchBar/SearchBar";
import Spinner from "../../../components/common/Spinner/Spinner";
import ingredientsService from "../../../services/ingredientsService";
import { parseApiError } from "../../../utils/apiErrors";

const MIN_TERM_LENGTH = 2;

/**
 * Search the ingredient catalogue and add results to the inventory.
 *
 * `query` is the committed (debounced) search; `result` is the answer to one
 * specific query. A query is "loading" until a result with the same id
 * arrives, which also discards out-of-order responses.
 */
export default function IngredientSearch({
    ownedIngredientIds,
    pendingIds,
    onAdd,
}) {
    const [text, setText] = useState("");
    const [query, setQuery] = useState({ id: 0, term: "" });
    const [result, setResult] = useState({ id: -1, items: [], error: null });

    useEffect(() => {
        if (!query.term) return undefined;

        const controller = new AbortController();

        ingredientsService
            .search(query.term, { signal: controller.signal })
            .then((items) => {
                if (controller.signal.aborted) return;

                setResult({ id: query.id, items, error: null });
            })
            .catch((error) => {
                if (controller.signal.aborted || error?.name === "AbortError") {
                    return;
                }

                setResult({
                    id: query.id,
                    items: [],
                    error: parseApiError(error).message,
                });
            });

        return () => controller.abort();
    }, [query]);

    function commit(value) {
        const term = value.trim();

        setQuery((current) => ({
            id: current.id + 1,
            term: term.length >= MIN_TERM_LENGTH ? term : "",
        }));
    }

    const hasQuery = query.term !== "";
    const loading = hasQuery && result.id !== query.id;
    const done = hasQuery && result.id === query.id;

    return (
        <div className="inventory-search">
            <SearchBar
                label="Add ingredients"
                placeholder="Search ingredients, e.g. egg"
                value={text}
                onChange={setText}
                onSearch={commit}
                loading={loading}
            />

            <div className="inventory-search__status" aria-live="polite">
                {!hasQuery && (
                    <p className="inventory-search__hint">
                        Type at least {MIN_TERM_LENGTH} letters to search.
                    </p>
                )}

                {loading && <Spinner size="sm" label="Searching ingredients..." />}

                {done && result.error && (
                    <p className="inventory-search__message" role="alert">
                        {result.error}{" "}
                        <Button
                            size="sm"
                            variant="ghost"
                            onClick={() =>
                                setQuery((current) => ({
                                    ...current,
                                    id: current.id + 1,
                                }))
                            }
                        >
                            Retry
                        </Button>
                    </p>
                )}

                {done && !result.error && result.items.length === 0 && (
                    <p className="inventory-search__hint">
                        No ingredients match &ldquo;{query.term}&rdquo;.
                    </p>
                )}
            </div>

            {done && !result.error && result.items.length > 0 && (
                <ul className="inventory-search__results">
                    {result.items.map((ingredient) => {
                        const owned = ownedIngredientIds.includes(ingredient.id);
                        const adding = pendingIds.includes(ingredient.id);

                        return (
                            <li
                                key={ingredient.id}
                                className="inventory-search__result"
                            >
                                <span className="inventory-search__name">
                                    {ingredient.name}
                                    {ingredient.category && (
                                        <span className="inventory-search__category">
                                            {ingredient.category}
                                        </span>
                                    )}
                                </span>

                                <Button
                                    size="sm"
                                    variant="secondary"
                                    disabled={owned || adding}
                                    onClick={() => onAdd(ingredient)}
                                    aria-label={
                                        owned
                                            ? `${ingredient.name} is already in your inventory`
                                            : `Add ${ingredient.name}`
                                    }
                                >
                                    {owned ? "Added" : adding ? "Adding..." : "Add"}
                                </Button>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}
