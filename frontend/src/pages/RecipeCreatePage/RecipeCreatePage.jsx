import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { RecipeForm } from "../../features/recipes";
import { useToast } from "../../hooks/useToast";
import recipeService from "../../services/api/recipeService";
import tagsApi from "../../services/TagsApi";
import { parseApiError } from "../../utils/apiErrors";

import "./RecipeCreatePage.css";

const toList = (data) =>
    Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

/**
 * Signed-in users add a recipe that's missing (Issue #67). The route is
 * wrapped in ProtectedRoute; the backend also refuses guests.
 * `?name=` pre-fills the name (used by the search page's no-results link).
 */
export default function RecipeCreatePage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { showToast } = useToast();

    const [tags, setTags] = useState([]);
    const [tagsError, setTagsError] = useState(false);

    useEffect(() => {
        const controller = new AbortController();

        tagsApi
            .getTags({ signal: controller.signal })
            .then((data) => setTags(toList(data)))
            .catch((error) => {
                if (error?.name !== "AbortError") setTagsError(true);
            });

        return () => controller.abort();
    }, []);

    async function handleSubmit(payload, image) {
        const recipe = await recipeService.createRecipe(payload);

        if (image) {
            try {
                await recipeService.uploadRecipeImage(recipe.id, image);
            } catch (error) {
                // The recipe itself is saved; only the photo failed.
                const reason = error?.data?.image?.[0] || parseApiError(error).message;
                showToast({
                    type: "error",
                    message: `Recipe added, but the photo couldn't be uploaded. ${reason}`,
                });
                navigate(`/recipes/${recipe.id}`);
                return;
            }
        }

        showToast({ type: "success", message: "Recipe added." });
        navigate(`/recipes/${recipe.id}`);
    }

    return (
        <section className="recipe-create-page">
            <header className="recipe-create-page__intro">
                <h1>Add a Recipe</h1>
                <p>Can&apos;t find a recipe you love? Add it so others can cook it too.</p>
            </header>

            {tagsError && (
                <p className="recipe-create-page__notice" role="status">
                    Tags couldn&apos;t be loaded. You can still add the recipe without them.
                </p>
            )}

            <RecipeForm
                tags={tags}
                initialName={searchParams.get("name") ?? ""}
                onSubmit={handleSubmit}
            />
        </section>
    );
}
