import { Link } from "react-router-dom";

import EmptyState from "../../components/common/EmptyState/EmptyState";
import ErrorState from "../../components/common/ErrorState/ErrorState";
import Spinner from "../../components/common/Spinner/Spinner";
import RecipeCard from "../../components/recipes/RecipeCard/RecipeCard";
import useRecipesForYou from "./hooks/useRecipesForYou";

import "./RecipesForYou.css";

const LINK_BUTTON = "recipes-for-you__link ui-button ui-button--md";

function Intro({ authenticated, personalized }) {
    if (personalized) {
        return (
            <>
                <h2 id="recipes-for-you-title">Recipes for You</h2>
                <p>Picked using your saved preferences.</p>
            </>
        );
    }

    if (authenticated) {
        return (
            <>
                <h2 id="recipes-for-you-title">Popular recipes</h2>
                <p>
                    <Link to="/profile">Add your preferences</Link> to get
                    recipes picked for you.
                </p>
            </>
        );
    }

    return (
        <>
            <h2 id="recipes-for-you-title">Explore recipes</h2>
            <p>
                <Link to="/login">Sign in</Link> and save your preferences to
                get recipes picked for you.
            </p>
        </>
    );
}

export default function RecipesForYou() {
    const { loading, authenticated, personalized, recipes, error, reload } =
        useRecipesForYou();

    let body;

    if (loading) {
        body = (
            <div className="recipes-for-you__center">
                <Spinner label="Loading recipes..." />
            </div>
        );
    } else if (error) {
        body = (
            <ErrorState
                title="Unable to load recipes"
                description={error}
                onRetry={reload}
            />
        );
    } else if (recipes.length === 0) {
        body = authenticated ? (
            <EmptyState
                icon="🍽️"
                title="No matching recipes yet"
                description="Nothing matches your saved preferences and allergies yet. Try adjusting them in your profile."
                action={
                    <Link
                        to="/profile"
                        className={`${LINK_BUTTON} ui-button--secondary`}
                    >
                        Edit profile
                    </Link>
                }
            />
        ) : (
            <EmptyState
                icon="🍽️"
                title="No recipes available yet"
                description="Check back soon."
            />
        );
    } else {
        body = (
            <>
                <div className="recipes-for-you__grid">
                    {recipes.map((recipe) => (
                        <RecipeCard key={recipe.id} recipe={recipe} />
                    ))}
                </div>

                <div className="recipes-for-you__more">
                    <Link
                        to="/recipes"
                        className={`${LINK_BUTTON} ui-button--primary`}
                    >
                        Browse all recipes
                    </Link>
                </div>
            </>
        );
    }

    return (
        <section className="recipes-for-you" aria-labelledby="recipes-for-you-title">
            <header className="recipes-for-you__header">
                {loading ? (
                    <h2 id="recipes-for-you-title">Recipes</h2>
                ) : (
                    <Intro
                        authenticated={authenticated}
                        personalized={personalized}
                    />
                )}
            </header>

            {body}

            {authenticated && !loading && !error && (
                <p className="recipes-for-you__notice">
                    * Allergen information is still being verified. Recipes
                    are not guaranteed to be allergen-free.
                </p>
            )}
        </section>
    );
}
