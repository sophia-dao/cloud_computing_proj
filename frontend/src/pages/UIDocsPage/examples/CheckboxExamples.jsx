
import { useState } from "react";
import Checkbox from "../../../components/common/Checkbox/Checkbox";

function CheckboxExamples() {
    const [preferences, setPreferences] = useState({
        vegetarian: false,
        vegan: false,
        glutenFree: true,
    });

    function handleChange(event) {
        const { name, checked } = event.target;

        setPreferences((current) => ({
            ...current,
            [name]: checked,
        }));
    }

    return (
        <div className="ui-docs__example-stack">
            <h4>Dietary Preferences</h4>

            <Checkbox
                name="vegetarian"
                label="Vegetarian"
                description="Exclude meat and seafood."
                checked={preferences.vegetarian}
                onChange={handleChange}
            />

            <Checkbox
                name="vegan"
                label="Vegan"
                description="Exclude all animal products."
                checked={preferences.vegan}
                onChange={handleChange}
            />

            <Checkbox
                name="glutenFree"
                label="Gluten-Free"
                checked={preferences.glutenFree}
                onChange={handleChange}
            />

            <h4>Disabled</h4>

            <Checkbox
                label="Unavailable Option"
                disabled
            />

            <h4>Validation Error</h4>

            <Checkbox
                label="Accept Terms"
                error="You must accept the terms to continue."
            />

            <pre>{JSON.stringify(preferences, null, 2)}</pre>
        </div>
    );
}

export default CheckboxExamples;
