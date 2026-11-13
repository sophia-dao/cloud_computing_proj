import { Link } from "react-router-dom";

import EmptyState from "../../../components/common/EmptyState/EmptyState";
import ErrorState from "../../../components/common/ErrorState/ErrorState";
import Spinner from "../../../components/common/Spinner/Spinner";

import "./RecommendationResults.css";

function formatScore(score) {
    const value = Number(score);
    if (!Number.isFinite(value)) return null;
    // Backend returns 0–1; display as a percentage without recalculating it.
    return `${Math.round(value * 100)}% match`;
}

function IngredientList({ title, items, variant }) {
    if (!items?.length) return null;

    return (
        <div className={`recommendation-card__ingredients recommendation-card__ingredients--${variant}`}>
            <span className="recommendation-card__ingredients-title">{title}</span>
            <span>{items.map((item) => item.name).join(", ")}</span>
        </div>
    );
}

export function RecommendationCard({ result }) {
    const recipe = result?.recipe ?? {};
    const score = formatScore(result?.match_score);

    return (
        <article className="recommendation-card">
            <Link to={`/recipes/${recipe.id}`} className="recommendation-card__link">
                <div className="recommendation-card__image">
                    {recipe.image ? (
                        <img src={recipe.image} alt={recipe.name} loading="lazy" />
                    ) : (
                        <span>No image available</span>
                    )}
                </div>

                <div className="recommendation-card__body">
                    {score && <span className="recommendation-card__score">{score}</span>}
                    <h3 className="recommendation-card__title">{recipe.name}</h3>

                    <IngredientList title="You have" items={result.available_ingredients} variant="available" />
                    <IngredientList title="Missing" items={result.missing_ingredients} variant="missing" />
                    <IngredientList title="Optional" items={result.optional_missing_ingredients} variant="optional" />
                </div>
            </Link>
        </article>
    );
}

/**
 * Renders the states of a recommendation request:
 * idle → loading → error | empty | results.
 */
export default function RecommendationResults({
    status = "idle",
    results = [],
    error = "",
    onRetry,
}) {
    if (status === "idle") return null;

    if (status === "loading") {
        return (
            <div className="recommendation-results__loading">
                <Spinner label="Finding recipes…" />
                <p>Finding recipes that use your ingredients…</p>
            </div>
        );
    }

    if (status === "error") {
        return (
            <ErrorState
                title="Couldn't load recommendations"
                description={error || "Please try again in a moment."}
                onRetry={onRetry}
            />
        );
    }

    if (!results.length) {
        return (
            <EmptyState
                icon="🍳"
                title="No matching recipes yet"
                description="Try adding more ingredients or switching to “Partial match”."
            />
        );
    }

    return (
        <section aria-label="Recommended recipes">
            <p className="recommendation-results__count">
                {results.length} recipe{results.length === 1 ? "" : "s"} found
            </p>
            <div className="recommendation-results__grid">
                {results.map((result, index) => (
                    <RecommendationCard
                        key={result?.recipe?.id ?? index}
                        result={result}
                    />
                ))}
            </div>
        </section>
    );
}
