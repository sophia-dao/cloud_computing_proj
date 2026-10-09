
import { useEffect, useId, useRef, useState } from "react";
import "./SearchBar.css";

function SearchBar({
    value,
    defaultValue = "",
    onChange,
    onSearch,
    onClear,
    placeholder = "Search...",
    label = "Search",
    debounce = 300,
    loading = false,
    disabled = false,
    showClear = true,
    className = "",
    ...props
}) {
    const generatedId = useId();
    const {
        id = generatedId,
        ...inputProps
    } = props;

    const isControlled = value !== undefined;

    const [internalValue, setInternalValue] = useState(defaultValue);
    const searchValue = isControlled ? value : internalValue;

    const searchCallbackRef = useRef(onSearch);
    const timerRef = useRef(null);
    const hasMounted = useRef(false);

    function handleSearch(event) {
        event.preventDefault();
        clearTimeout(timerRef.current);
        timerRef.current = null;
        onSearch?.(searchValue);
    }


    // Keep the latest callback without restarting the debounce timer.
    useEffect(() => {
        searchCallbackRef.current = onSearch;
    }, [onSearch]);

    useEffect(() => {
        if (!hasMounted.current) {
            hasMounted.current = true;
            return;
        }

        if (!searchCallbackRef.current) return;

        timerRef.current = setTimeout(() => {
            searchCallbackRef.current?.(searchValue);
            timerRef.current = null;
        }, debounce);

        return () => {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        };
    }, [searchValue, debounce]);


    function handleChange(event) {
        const nextValue = event.target.value;

        if (!isControlled) {
            setInternalValue(nextValue);
        }

        onChange?.(nextValue);
    }

    function handleClear() {
        if (!isControlled) {
            setInternalValue("");
        }

        onChange?.("");
        onClear?.();

        // The value update will trigger debounced search with "".
    }

    return (
        <form
            className={[
                "ui-search-bar",
                className,
            ].filter(Boolean).join(" ")}
            role="search"
            onSubmit={handleSearch}
        >
            <label
                htmlFor={id}
                className="ui-search-bar__label"
            >
                {label}
            </label>

            <div className="ui-search-bar__field">
                <svg
                    className="ui-search-bar__icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                >
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20 20-4-4" />
                </svg>

                <input
                    {...inputProps}
                    id={id}
                    type="search"
                    value={searchValue}
                    onChange={handleChange}
                    placeholder={placeholder}
                    disabled={disabled}
                    className="ui-search-bar__input"
                />

                {loading && (
                    <span
                        className="ui-search-bar__spinner"
                        aria-label="Searching"
                        role="status"
                    />
                )}

                {showClear && searchValue && !disabled && (
                    <button
                        type="button"
                        className="ui-search-bar__clear"
                        aria-label="Clear search"
                        onClick={handleClear}
                    >
                        ×
                    </button>
                )}
            </div>
        </form>
    );
}

export default SearchBar;
