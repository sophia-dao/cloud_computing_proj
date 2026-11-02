
import { Link } from "react-router-dom";
import "./RecipeCard.css";

export default function RecipeCard({ recipe }) {
    const cuisine = recipe.tags?.find(
        (tag) => tag.type === "CUISINE"
    );

    const category = recipe.tags?.find(
        (tag) => tag.type === "OTHER"
    );

    return (
        <article className="recipe-tile">
            <Link
                to={`/recipes/${recipe.id}`}
                className="recipe-tile__link"
            >
                <div className="recipe-tile__image-wrapper">
                    {recipe.image ? (
                        <img
                            src={recipe.image}
                            alt={recipe.name}
                            loading="lazy"
                            className="recipe-tile__image"
                        />
                    ) : (
                        <div className="recipe-tile__placeholder">
                            No image available
                        </div>
                    )}
                </div>

                <div className="recipe-tile__content">
                    <p className="recipe-tile__metadata">
                        {[cuisine?.name, category?.name]
                            .filter(Boolean)
                            .join(" · ") || "RECIPE"}
                    </p>

                    <h2 className="recipe-tile__title">
                        {recipe.name}
                    </h2>

                    <span className="recipe-tile__action">
                        View recipe <span aria-hidden="true">↗</span>
                    </span>
                </div>
            </Link>
        </article>
    );
}
