
import { useState } from "react";

import Badge from "../../../components/common/Badge/Badge";
import Button from "../../../components/common/Button/Button";

function BadgeExamples() {
    const [ingredients, setIngredients] = useState([
        "Tomato",
        "Chicken",
        "Rice",
    ]);

    function removeIngredient(name) {
        setIngredients((current) =>
            current.filter((ingredient) => ingredient !== name)
        );
    }

    function resetIngredients() {
        setIngredients(["Tomato", "Chicken", "Rice"]);
    }

    return (
        <div className="ui-docs__example-stack">
            <h4>Variants</h4>

            <div className="ui-docs__example-row">
                <Badge>Neutral</Badge>
                <Badge variant="success">Available</Badge>
                <Badge variant="warning">Partial Match</Badge>
                <Badge variant="danger">Contains Allergen</Badge>
                <Badge variant="accent">Vietnamese</Badge>
            </div>

            <h4>Sizes</h4>

            <div className="ui-docs__example-row">
                <Badge size="sm">Small</Badge>
                <Badge size="md">Medium</Badge>
            </div>

            <h4>Removable Ingredient Tags</h4>

            <div className="ui-docs__example-row">
                {ingredients.map((ingredient) => (
                    <Badge
                        key={ingredient}
                        variant="accent"
                        removable
                        onRemove={() => removeIngredient(ingredient)}
                    >
                        {ingredient}
                    </Badge>
                ))}
            </div>

            <Button
                variant="secondary"
                size="sm"
                onClick={resetIngredients}
            >
                Reset Ingredients
            </Button>

            <h4>Disabled</h4>

            <Badge removable disabled>
                Disabled Tag
            </Badge>
        </div>
    );
}

export default BadgeExamples;
