import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Button from "../../components/common/Button/Button";
import EmptyState from "../../components/common/EmptyState/EmptyState";
import ErrorState from "../../components/common/ErrorState/ErrorState";
import Spinner from "../../components/common/Spinner/Spinner";
import RecipeCard from "../../components/recipes/RecipeCard/RecipeCard";
import { useToast } from "../../hooks/useToast";
import recipeService from "../../services/api/recipeService";
import { parseApiError } from "../../utils/apiErrors";

import "./SavedRecipesPage.css";

/** The signed-in user's saved recipes, newest first (Issue #14). */
export default function SavedRecipesPage() {
    const { showToast } = useToast();

    const [page, setPage] = useState(1);
    const [reloadKey, setReloadKey] = useState(0);
    const [result, setResult] = useState({
        key: "",
        items: [],
        count: 0,
        hasNext: false,
        error: "",
    });
    const [removing, setRemoving] = useState([]);

    const requestKey = `${page}:${reloadKey}`;

    useEffect(() => {
        const controller = new AbortController();

        recipeService
            .getSavedRecipes({ page, signal: controller.signal })
            .then((data) => {
                if (controller.signal.aborted) return;

                setResult({
                    key: requestKey,
                    items: Array.isArray(data?.results) ? data.results : [],
                    count: data?.count ?? 0,
                    hasNext: Boolean(data?.next),
                    error: "",
                });
            })
            .catch((error) => {
                if (controller.signal.aborted || error?.name === "AbortError") return;

                if (error?.status === 404 && page > 1) {
                    // The page no longer exists (items were removed): go back one.
                    setPage((current) => current - 1);
                    return;
                }

                setResult({
                    key: requestKey,
                    items: [],
                    count: 0,
                    hasNext: false,
                    error: parseApiError(error).message,
                });
            });

        return () => controller.abort();
    }, [page, requestKey]);

    const reload = useCallback(() => setReloadKey((key) => key + 1), []);

    async function remove(entry) {
        setRemoving((ids) => [...ids, entry.id]);

        try {
            await recipeService.unsaveRecipe(entry.id);
        } catch (error) {
            if (error?.status !== 404) {
                showToast({
                    type: "error",
                    message: `Couldn't remove ${entry.recipe.name}. ${parseApiError(error).message}`,
                });
                setRemoving((ids) => ids.filter((id) => id !== entry.id));
                return;
            }
        }

        setRemoving((ids) => ids.filter((id) => id !== entry.id));
        // Reload so the page refills from the next one.
        reload();
    }

    const loading = result.key !== requestKey;

    let content;

    if (loading && result.items.length === 0) {
        content = (
            <div className="saved-recipes-page__center">
                <Spinner label="Loading your saved recipes..." />
            </div>
        );
    } else if (result.error) {
        content = (
            <ErrorState
                title="Unable to load your saved recipes"
                description={result.error}
                onRetry={reload}
            />
        );
    } else if (result.items.length === 0) {
        content = (
            <EmptyState
                icon="☆"
                title="No saved recipes yet"
                description="Open any recipe and choose Save recipe to keep it here."
                action={
                    <Link
                        to="/recipes"
                        className="saved-recipes-page__link ui-button ui-button--primary ui-button--md"
                    >
                        Browse recipes
                    </Link>
                }
            />
        );
    } else {
        content = (
            <>
                <p className="saved-recipes-page__count">
                    {result.count} saved {result.count === 1 ? "recipe" : "recipes"}
                </p>

                <ul className="saved-recipes-page__grid">
                    {result.items.map((entry) => (
                        <li key={entry.id} className="saved-recipes-page__item">
                            <RecipeCard recipe={entry.recipe} />
                            <Button
                                variant="ghost"
                                size="sm"
                                disabled={removing.includes(entry.id)}
                                aria-label={`Remove ${entry.recipe.name} from saved recipes`}
                                onClick={() => remove(entry)}
                            >
                                {removing.includes(entry.id) ? "Removing..." : "Remove"}
                            </Button>
                        </li>
                    ))}
                </ul>

                {(page > 1 || result.hasNext) && (
                    <nav className="saved-recipes-page__pagination" aria-label="Saved recipes pages">
                        <Button
                            variant="secondary"
                            disabled={page === 1 || loading}
                            onClick={() => setPage((current) => current - 1)}
                        >
                            Previous
                        </Button>
                        <span>Page {page}</span>
                        <Button
                            variant="secondary"
                            disabled={!result.hasNext || loading}
                            onClick={() => setPage((current) => current + 1)}
                        >
                            Next
                        </Button>
                    </nav>
                )}
            </>
        );
    }

    return (
        <section className="saved-recipes-page">
            <h1>Saved Recipes</h1>
            {content}
        </section>
    );
}
