
import { useEffect, useRef, useState } from "react";
import Checkbox from "../Checkbox/Checkbox";
import "./MultiSelect.css";

export default function MultiSelect({
    label,
    placeholder = "Select options...",
    options = [],
    value = [],
    onChange,
    disabled = false,
}) {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState("");
    const containerRef = useRef(null);

    const selectedOptions = options.filter((option) =>
        value.includes(option.value)
    );

    const filteredOptions = options.filter((option) =>
        option.label.toLowerCase().includes(search.toLowerCase())
    );

    useEffect(() => {
        function handleClickOutside(event) {
            if (
                containerRef.current &&
                !containerRef.current.contains(event.target)
            ) {
                setIsOpen(false);
            }
        }

        function handleEscape(event) {
            if (event.key === "Escape") {
                setIsOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);
        document.addEventListener("keydown", handleEscape);

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
            document.removeEventListener("keydown", handleEscape);
        };
    }, []);

    function toggleOption(optionValue) {
        if (value.includes(optionValue)) {
            onChange(value.filter((item) => item !== optionValue));
        } else {
            onChange([...value, optionValue]);
        }
    }

    function clearSelection() {
        onChange([]);
    }

    function toggleDropdown() {
        if (disabled) return;

        setIsOpen((previous) => !previous);
        setSearch("");
    }

    return (
        <div
            className="ui-multi-select"
            ref={containerRef}
        >
            {label && (
                <span className="ui-multi-select__label">
                    {label}
                </span>
            )}

            <button
                type="button"
                className={`ui-multi-select__trigger ${isOpen ? "ui-multi-select__trigger--open" : ""
                    }`}
                onClick={toggleDropdown}
                disabled={disabled}
                aria-expanded={isOpen}
                aria-haspopup="true"
            >
                <span className="ui-multi-select__value">
                    {selectedOptions.length === 0 ? (
                        <span className="ui-multi-select__placeholder">
                            {placeholder}
                        </span>
                    ) : (
                        <span className="ui-multi-select__chips">
                            {selectedOptions.map((option) => (
                                <span
                                    key={option.value}
                                    className="ui-multi-select__chip"
                                >
                                    {option.label}
                                </span>
                            ))}
                        </span>
                    )}
                </span>

                <span
                    className={`ui-multi-select__arrow ${isOpen ? "ui-multi-select__arrow--open" : ""
                        }`}
                    aria-hidden="true"
                >
                    ▾
                </span>
            </button>

            {isOpen && (
                <div className="ui-multi-select__dropdown">
                    <input
                        type="search"
                        className="ui-multi-select__search"
                        placeholder="Search..."
                        value={search}
                        onChange={(event) =>
                            setSearch(event.target.value)
                        }
                        aria-label={`Search ${label || "options"}`}
                    />

                    <div className="ui-multi-select__options">
                        {filteredOptions.length > 0 ? (
                            filteredOptions.map((option) => (
                                <div
                                    key={option.value}
                                    className="ui-multi-select__option"
                                >
                                    <Checkbox
                                        label={option.label}
                                        checked={value.includes(option.value)}
                                        onChange={() =>
                                            toggleOption(option.value)
                                        }
                                    />
                                </div>
                            ))
                        ) : (
                            <p className="ui-multi-select__empty">
                                No matching options.
                            </p>
                        )}
                    </div>

                    <div className="ui-multi-select__footer">
                        <span>
                            {value.length} selected
                        </span>

                        <button
                            type="button"
                            className="ui-multi-select__clear"
                            onClick={clearSelection}
                            disabled={value.length === 0}
                        >
                            Clear selection
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
