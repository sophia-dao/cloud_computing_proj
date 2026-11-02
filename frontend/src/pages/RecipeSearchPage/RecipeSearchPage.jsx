
import { useEffect, useState } from "react";

import RecipeCard from "../../components/recipes/RecipeCard/RecipeCard";
import SearchBar from "../../components/common/SearchBar/SearchBar";
import Spinner from "../../components/common/Spinner/Spinner";
import Button from "../../components/common/Button/Button";
import recipesApi from "../../services/RecipesApi";
import tagsApi from "../../services/TagsApi";
import Select from "../../components/common/Select/Select";
import { buildTagOptions } from "../../utils/tagUtils";

import "./RecipeSearchPage.css";

export default function RecipeSearchPage() {
    const [recipes, setRecipes] = useState([]);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [hasNextPage, setHasNextPage] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [retryKey, setRetryKey] = useState(0);

    const [searchInput, setSearchInput] = useState("");
    const [searchQuery, setSearchQuery] = useState("");

    const [filters, setFilters] = useState({
        cuisine: "",
        diet: "",
        cost: "",
        other: "",
    });

    const [tags, setTags] = useState([]);
    const [tagsLoading, setTagsLoading] = useState(true);
    const [tagsError, setTagsError] = useState("");

    const cuisineOptions = buildTagOptions(
        tags, "CUISINE", "All cuisines"
    );

    const dietOptions = buildTagOptions(
        tags, "DIET", "All diets"
    );

    const costOptions = buildTagOptions(
        tags, "COST", "Any cost"
    );

    const categoryOptions = buildTagOptions(
        tags, "OTHER", "All categories"
    );

    useEffect(() => {
        const controller = new AbortController();

        async function loadTags() {
            try {
                const data = await tagsApi.getTags({
                    signal: controller.signal,
                });

                if (!controller.signal.aborted) {
                    setTags(data);
                }
            } catch (err) {
                if (!controller.signal.aborted) {
                    setTagsError("Unable to load recipe filters.");
                }
            } finally {
                if (!controller.signal.aborted) {
                    setTagsLoading(false);
                }
            }
        }

        loadTags();

        return () => controller.abort();
    }, []);

    function handleFilterChange(name, value) {
        setFilters((current) => ({
            ...current,
            [name]: value,
        }));
        setPage(1);
    }

    function clearFilters() {
        setFilters({
            cuisine: "",
            diet: "",
            cost: "",
            other: "",
        });
        setPage(1);
    }

    const handleSearch = (value) => {
        setSearchQuery((value ?? searchInput).trim());
        setPage(1);
    };

    useEffect(() => {
        const controller = new AbortController();

        async function loadRecipes() {
            setLoading(true);
            setError("");

            try {
                const data = await recipesApi.getRecipes({
                    page,
                    search: searchQuery,
                    ...filters,
                    signal: controller.signal,
                });

                if (controller.signal.aborted) return;

                setRecipes(data.results || []);
                setTotalCount(data.count || 0);
                setHasNextPage(Boolean(data.next));
            } catch (err) {
                if (err.name !== "AbortError") {
                    setError(err.message || "Failed to load recipes.");
                }
            } finally {
                if (!controller.signal.aborted) {
                    setLoading(false);
                }
            }
        }

        loadRecipes();

        return () => controller.abort();
    }, [page, searchQuery, filters, retryKey]);

    return (
        <section className="recipe-search-page">
            <header className="recipe-search-page__header">
                <span className="recipe-search-page__eyebrow">
                    THE RECIPE COLLECTION
                </span>

                <h1>What are you craving?</h1>

                <p>
                    Explore delicious recipes, discover new flavors,
                    and find inspiration for your next meal.
                </p>
            </header>


            <div className="recipe-search-page__toolbar">
                <div className="recipe-search-page__search">
                    <SearchBar
                        label="Search recipes"
                        placeholder="Try pasta, chicken, soup..."
                        value={searchInput}
                        onChange={setSearchInput}
                        onSearch={handleSearch}
                        debounce={300}
                    />
                </div>

                <div className="recipe-search-page__filter-heading">
                    <span className="recipe-search-page__filter-title">
                        Refine results
                    </span>

                    <Button
                        variant="secondary"
                        disabled={!Object.values(filters).some(Boolean)}
                        onClick={clearFilters}
                    >
                        Clear all
                    </Button>
                </div>

                <div className="recipe-search-page__filters">
                    {cuisineOptions.length > 1 && (
                        <Select
                            label="Cuisine"
                            name="cuisine"
                            value={filters.cuisine}
                            onChange={(event) =>
                                handleFilterChange("cuisine", event.target.value)
                            }
                            options={cuisineOptions}
                        />
                    )}

                    {dietOptions.length > 1 && (
                        <Select
                            label="Diet"
                            name="diet"
                            value={filters.diet}
                            onChange={(event) =>
                                handleFilterChange("diet", event.target.value)
                            }
                            options={dietOptions}
                        />
                    )}

                    {costOptions.length > 1 && (
                        <Select
                            label="Cost"
                            name="cost"
                            value={filters.cost}
                            onChange={(event) =>
                                handleFilterChange("cost", event.target.value)
                            }
                            options={costOptions}
                        />
                    )}

                    {categoryOptions.length > 1 && (
                        <Select
                            label="Category"
                            name="other"
                            value={filters.other}
                            onChange={(event) =>
                                handleFilterChange("other", event.target.value)
                            }
                            options={categoryOptions}
                        />
                    )}
                </div>

                {tagsLoading && (
                    <p className="recipe-search-page__filter-status">
                        Loading filters...
                    </p>
                )}

                {tagsError && (
                    <p className="recipe-search-page__filter-status" role="alert">
                        {tagsError}
                    </p>
                )}
            </div>

            <div className="recipe-search-page__results-header">
                <h2>Explore recipes</h2>

                {!loading && !error && (
                    <span>
                        {totalCount} {totalCount === 1 ? "recipe" : "recipes"}
                    </span>
                )}
            </div>

            {loading ? (
                <div className="recipe-search-page__status">
                    <Spinner size="md" label="Loading recipes..." />
                </div>
            ) : error ? (
                <div className="recipe-search-page__status" role="alert">
                    <p>{error}</p>
                    <Button onClick={() => setRetryKey((key) => key + 1)}>
                        Try again
                    </Button>
                </div>
            ) : recipes.length === 0 ? (
                <div className="recipe-search-page__status">
                    <p>
                        {searchQuery
                            ? `No recipes found for "${searchQuery}".`
                            : "No recipes available."}
                    </p>
                </div>
            ) : (
                <>
                    <div className="recipe-search-page__grid">
                        {recipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.id}
                                recipe={recipe}
                            />
                        ))}
                    </div>

                    <nav
                        className="recipe-search-page__pagination"
                        aria-label="Recipe pagination"
                    >
                        <Button
                            variant="secondary"
                            disabled={page === 1}
                            onClick={() => setPage((p) => p - 1)}
                        >
                            Previous
                        </Button>

                        <span>Page {page}</span>

                        <Button
                            variant="secondary"
                            disabled={!hasNextPage}
                            onClick={() => setPage((p) => p + 1)}
                        >
                            Next
                        </Button>
                    </nav>
                </>
            )}
        </section>
    );
}
