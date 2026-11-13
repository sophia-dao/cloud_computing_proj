import { useId, useRef, useState } from "react";

import Badge from "../../../components/common/Badge/Badge";
import useIngredientSearch, {
    MIN_INGREDIENT_QUERY_LENGTH,
} from "../hooks/useIngredientSearch";

import "./IngredientPicker.css";

/**
 * Autocomplete input for canonical ingredients plus removable chips
 * for the current selection. Selection state is owned by the parent
 * (see useIngredientSelection) so it can be submitted elsewhere.
 */
export default function IngredientPicker({
    selected = [],
    onAdd,
    onRemove,
    onClear,
    label = "Ingredients you have",
    placeholder = "Search ingredients, e.g. egg, rice, garlic",
    disabled = false,
}) {
    const inputId = useId();
    const listboxId = `${inputId}-listbox`;
    const statusId = `${inputId}-status`;
    const inputRef = useRef(null);

    const [query, setQuery] = useState("");
    const [open, setOpen] = useState(false);
    const [activeIndex, setActiveIndex] = useState(-1);

    const { results, loading, error, isSearchable, settled } =
        useIngredientSearch(query);

    const selectedIds = new Set(selected.map((item) => item.id));
    const showList = open && isSearchable;

    function choose(ingredient) {
        if (!ingredient) return;

        // Picking an ingredient that's already selected just closes the list.
        if (!selectedIds.has(ingredient.id)) onAdd?.(ingredient);
        setQuery("");
        setActiveIndex(-1);
        setOpen(false);
        inputRef.current?.focus();
    }

    function handleKeyDown(event) {
        if (event.key === "ArrowDown") {
            event.preventDefault();
            setOpen(true);
            setActiveIndex((index) =>
                results.length ? (index + 1) % results.length : -1
            );
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActiveIndex((index) =>
                results.length
                    ? (index - 1 + results.length) % results.length
                    : -1
            );
        } else if (event.key === "Enter") {
            // Never submit a surrounding form from the search box.
            event.preventDefault();
            const target = results[activeIndex] ??
                (results.length === 1 ? results[0] : null);
            choose(target);
        } else if (event.key === "Escape") {
            setOpen(false);
            setActiveIndex(-1);
        } else if (
            event.key === "Backspace" &&
            query === "" &&
            selected.length > 0
        ) {
            onRemove?.(selected[selected.length - 1].id);
        }
    }

    let statusMessage = "";
    if (showList) {
        if (loading) statusMessage = "Searching…";
        else if (error) statusMessage = error;
        else if (settled && results.length === 0)
            statusMessage = `No ingredients match “${query.trim()}”.`;
        else if (settled)
            statusMessage = `${results.length} ingredient${results.length === 1 ? "" : "s"} found.`;
    }

    const activeOptionId =
        showList && activeIndex >= 0 && results[activeIndex]
            ? `${listboxId}-${results[activeIndex].id}`
            : undefined;

    return (
        <div className="ingredient-picker">
            <label htmlFor={inputId} className="ingredient-picker__label">
                {label}
            </label>

            <div className="ingredient-picker__field">
                <input
                    ref={inputRef}
                    id={inputId}
                    type="text"
                    role="combobox"
                    autoComplete="off"
                    className="ingredient-picker__input"
                    placeholder={placeholder}
                    value={query}
                    disabled={disabled}
                    aria-expanded={showList}
                    aria-controls={listboxId}
                    aria-autocomplete="list"
                    aria-activedescendant={activeOptionId}
                    aria-describedby={statusId}
                    maxLength={255}
                    onChange={(event) => {
                        setQuery(event.target.value);
                        setActiveIndex(-1);
                        setOpen(true);
                    }}
                    onFocus={() => setOpen(true)}
                    onBlur={() => setOpen(false)}
                    onKeyDown={handleKeyDown}
                />

                {loading && showList && (
                    <span className="ingredient-picker__spinner" aria-hidden="true" />
                )}

                <ul
                    id={listboxId}
                    role="listbox"
                    aria-label="Ingredient suggestions"
                    className="ingredient-picker__listbox"
                    hidden={!showList || (!results.length && !statusMessage)}
                >
                    {results.map((ingredient, index) => {
                        const alreadySelected = selectedIds.has(ingredient.id);

                        return (
                            <li
                                key={ingredient.id}
                                id={`${listboxId}-${ingredient.id}`}
                                role="option"
                                aria-selected={index === activeIndex}
                                aria-disabled={alreadySelected}
                                className={[
                                    "ingredient-picker__option",
                                    index === activeIndex && "ingredient-picker__option--active",
                                    alreadySelected && "ingredient-picker__option--selected",
                                ].filter(Boolean).join(" ")}
                                // mousedown keeps focus in the input (blur would close the list first)
                                onMouseDown={(event) => {
                                    event.preventDefault();
                                    choose(ingredient);
                                }}
                                onMouseEnter={() => setActiveIndex(index)}
                            >
                                <span>{ingredient.name}</span>
                                <span className="ingredient-picker__option-meta">
                                    {alreadySelected ? "Added" : ingredient.category}
                                </span>
                            </li>
                        );
                    })}

                    {statusMessage && !results.length && (
                        <li className="ingredient-picker__message" role="presentation">
                            {statusMessage}
                        </li>
                    )}
                </ul>
            </div>

            <p id={statusId} className="ingredient-picker__hint" aria-live="polite">
                {showList && statusMessage
                    ? statusMessage
                    : `Type at least ${MIN_INGREDIENT_QUERY_LENGTH} letters to search.`}
            </p>

            <div className="ingredient-picker__selection">
                {selected.length === 0 ? (
                    <p className="ingredient-picker__empty">
                        No ingredients selected yet.
                    </p>
                ) : (
                    <>
                        <ul className="ingredient-picker__chips" aria-label="Selected ingredients">
                            {selected.map((ingredient) => (
                                <li key={ingredient.id}>
                                    <Badge
                                        variant="accent"
                                        removable
                                        disabled={disabled}
                                        onRemove={() => onRemove?.(ingredient.id)}
                                    >
                                        {ingredient.name}
                                    </Badge>
                                </li>
                            ))}
                        </ul>

                        {onClear && (
                            <button
                                type="button"
                                className="ingredient-picker__clear"
                                onClick={onClear}
                                disabled={disabled}
                            >
                                Clear all
                            </button>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
