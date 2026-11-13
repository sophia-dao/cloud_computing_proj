
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import recipesApi from "../../services/recipesApi";
import Checkbox from "../../components/common/Checkbox/Checkbox";
import Badge from "../../components/common/Badge/Badge";
import { SaveRecipeButton } from "../../features/recipes";

import "./RecipeDetailPage.css";

// Format quantities without unnecessary decimals.
function formatQuantity(value) {
    if (value == null || value === "") return "";

    const number = Number(value);

    return Number.isFinite(number)
        ? String(number)
        : String(value);
}

// Format an ingredient from the Django API.
function formatIngredient(item) {
    const name = item.ingredient?.name ?? "Unknown ingredient";

    const quantity = formatQuantity(item.quantity);
    const unit = item.unit?.trim() ?? "";
    const notes = item.notes?.trim() ?? "";

    const amount = [quantity, unit].filter(Boolean).join(" ");

    return {
        name,
        measurement: amount || notes,
        optional: Boolean(item.is_optional),
        notes: amount ? notes : "",
    };
}

// Split instructions into paragraphs without step numbers.
function parseInstructions(instructions) {
    if (!instructions?.trim()) return [];

    const normalized = instructions
        .replace(/\r\n?/g, "\n")
        .trim();

    // Handle "Step 1", "Step 2", etc.
    const explicitSteps = normalized
        .split(/(?:^|\n)\s*step\s+\d+\s*[:.)-]?\s*/i)
        .map((paragraph) => paragraph.trim())
        .filter(Boolean);

    if (explicitSteps.length > 1) {
        return explicitSteps;
    }

    // Otherwise split by line breaks.
    return normalized
        .split(/\n+/)
        .map((paragraph) => paragraph.trim())
        .filter(Boolean);
}

// Map Django tag types to the shared Badge variants.
function getTagVariant(type) {
    switch (type) {
        case "CUISINE":
            return "accent";
        case "DIET":
            return "success";
        case "COST":
            return "warning";
        default:
            return "default";
    }
}

export default function RecipeDetailPage() {
    const { id } = useParams();

    const [recipe, setRecipe] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [checkedIngredients, setCheckedIngredients] = useState([]);

    useEffect(() => {
        const controller = new AbortController();

        async function loadRecipe() {
            setLoading(true);
            setError("");
            setRecipe(null);
            setCheckedIngredients([]);

            try {
                const response = await recipesApi.getRecipeById(id, {
                    signal: controller.signal,
                });

                if (!controller.signal.aborted) {
                    setRecipe(response.data ?? response);
                }
            } catch (err) {
                if (controller.signal.aborted) return;

                if (err.response?.status === 404) {
                    setError("Recipe not found.");
                } else {
                    setError(
                        "Unable to load this recipe. Please try again."
                    );
                }
            } finally {
                if (!controller.signal.aborted) {
                    setLoading(false);
                }
            }
        }

        loadRecipe();

        return () => controller.abort();
    }, [id]);

    function toggleIngredient(index) {
        setCheckedIngredients((previous) =>
            previous.includes(index)
                ? previous.filter((item) => item !== index)
                : [...previous, index]
        );
    }

    if (loading) {
        return (
            <main className="recipe-detail-page">
                <div className="recipe-detail-state">
                    <p>Loading recipe...</p>
                </div>
            </main>
        );
    }

    if (error || !recipe) {
        return (
            <main className="recipe-detail-page">
                <div className="recipe-detail-state">
                    <h2>{error || "Recipe unavailable"}</h2>
                    <Link to="/recipes" className="recipe-detail-back">
                        Back to recipes
                    </Link>
                </div>
            </main>
        );
    }

    const ingredients = recipe.ingredients ?? [];
    const paragraphs = parseInstructions(recipe.instructions);

    const hasDescription =
        recipe.description &&
        !recipe.description.startsWith("Imported from TheMealDB");

    const hasTime =
        recipe.preparation_time != null ||
        recipe.cooking_time != null;

    return (
        <main className="recipe-detail-page">
            <Link to="/recipes" className="recipe-detail-back">
                ← Back to recipes
            </Link>

            <article className="recipe-detail-container">
                {/* Recipe image */}
                <div className="recipe-detail-hero">
                    {recipe.image ? (
                        <img
                            src={recipe.image}
                            alt={recipe.name}
                            className="recipe-detail-image"
                        />
                    ) : (
                        <div className="recipe-detail-image-placeholder">
                            No image available
                        </div>
                    )}
                </div>

                {/* Recipe header */}
                <header className="recipe-detail-header">
                    <h1>{recipe.name}</h1>

                    <SaveRecipeButton recipeId={recipe.id} />

                    {recipe.tags?.length > 0 && (
                        <div className="recipe-detail-tags">
                            {recipe.tags.map((tag) => (
                                <Badge
                                    key={tag.id}
                                    variant={getTagVariant(tag.type)}
                                >
                                    {tag.name}
                                </Badge>
                            ))}
                        </div>
                    )}

                    {hasDescription && (
                        <p className="recipe-detail-description">
                            {recipe.description}
                        </p>
                    )}

                    {hasTime && (
                        <div className="recipe-detail-meta">
                            {recipe.preparation_time != null && (
                                <span>
                                    Prep: {recipe.preparation_time} min
                                </span>
                            )}

                            {recipe.cooking_time != null && (
                                <span>
                                    Cook: {recipe.cooking_time} min
                                </span>
                            )}
                        </div>
                    )}
                </header>

                {/* Ingredients and instructions */}
                <div className="recipe-detail-content">
                    <section className="recipe-detail-ingredients">
                        <h2>Ingredients</h2>

                        <p className="recipe-detail-section-subtitle">
                            {ingredients.length} ingredients
                        </p>

                        {ingredients.length === 0 ? (
                            <p>No ingredients available.</p>
                        ) : (
                            <ul className="recipe-detail-ingredient-list">
                                {ingredients.map((item, index) => {
                                    const ingredient = formatIngredient(item);
                                    const checked =
                                        checkedIngredients.includes(index);

                                    const label = [
                                        ingredient.measurement,
                                        ingredient.name,
                                        ingredient.optional
                                            ? "(optional)"
                                            : "",
                                    ]
                                        .filter(Boolean)
                                        .join(" ");

                                    return (
                                        <li key={index}>
                                            <div
                                                className={
                                                    "recipe-detail-ingredient" +
                                                    (checked ? " checked" : "")
                                                }
                                            >
                                                <Checkbox
                                                    label={label}
                                                    checked={checked}
                                                    onChange={() =>
                                                        toggleIngredient(index)
                                                    }
                                                />

                                                {ingredient.notes && (
                                                    <small className="recipe-detail-ingredient-notes">
                                                        {ingredient.notes}
                                                    </small>
                                                )}
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </section>

                    <section className="recipe-detail-instructions">
                        <h2>Instructions</h2>

                        {paragraphs.length === 0 ? (
                            <p>No instructions available.</p>
                        ) : (
                            <div className="recipe-detail-paragraphs">
                                {paragraphs.map((paragraph, index) => (
                                    <p key={index}>{paragraph}</p>
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            </article>
        </main>
    );
}
