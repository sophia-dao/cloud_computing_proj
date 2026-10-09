
import { useState } from "react";
import SearchBar from "../../../components/common/SearchBar/SearchBar";

function SearchBarExamples() {
    const [query, setQuery] = useState("");
    const [lastSearch, setLastSearch] = useState("");
    const [loading, setLoading] = useState(false);

    return (
        <div className="ui-docs__example-stack">
            <SearchBar
                label="Search Ingredients"
                placeholder="Try tomato, chicken, or rice..."
                value={query}
                onChange={setQuery}
                onSearch={setLastSearch}
                debounce={400}
            />

            <p>
                Current input: <strong>{query || "(empty)"}</strong>
            </p>

            <p>
                Last search: <strong>{lastSearch || "(none)"}</strong>
            </p>

            <SearchBar
                label="Loading Example"
                placeholder="Searching recipes..."
                loading={loading}
                onSearch={() => { }}
            />

            <button
                type="button"
                onClick={() => setLoading((current) => !current)}
            >
                Toggle Loading
            </button>

            <SearchBar
                label="Disabled Example"
                placeholder="Search unavailable"
                disabled
            />
        </div>
    );
}

export default SearchBarExamples;
