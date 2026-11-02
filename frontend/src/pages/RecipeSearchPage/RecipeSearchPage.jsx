
import { useEffect, useState } from "react";

import RecipeCard from "../../components/recipes/RecipeCard/RecipeCard";
import SearchBar from "../../components/common/SearchBar/SearchBar";
import Spinner from "../../components/common/Spinner/Spinner";
import Button from "../../components/common/Button/Button";
import recipesApi from "../../services/RecipesApi";

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

    useEffect(() => {
        const controller = new AbortController();

        async function loadRecipes() {
            setLoading(true);
            setError("");

            try {
                const data = await recipesApi.getRecipes({
                    page,
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
    }, [page, retryKey]);

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
                <SearchBar
                    label="Search recipes"
                    placeholder="Try pasta, chicken, soup..."
                    value={searchInput}
                    onChange={setSearchInput}
                    onSearch={() => { }}
                    debounce={300}
                />
            </div>

            <div className="recipe-search-page__results-header">
                <h2>Explore recipes</h2>

                {!loading && !error && (
                    <span>{totalCount} recipes</span>
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
                    <p>No recipes available.</p>
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
