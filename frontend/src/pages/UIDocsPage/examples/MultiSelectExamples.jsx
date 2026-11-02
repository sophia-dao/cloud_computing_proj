
import { useState } from "react";

import MultiSelect from "../../../components/common/MultiSelect/MultiSelect";

const allergenOptions = [
    { label: "Milk", value: "Milk" },
    { label: "Egg", value: "Egg" },
    { label: "Peanut", value: "Peanut" },
    { label: "Tree Nuts", value: "Tree Nuts" },
    { label: "Wheat", value: "Wheat" },
    { label: "Soy", value: "Soy" },
    { label: "Fish", value: "Fish" },
    { label: "Shellfish", value: "Shellfish" },
];

function MultiSelectExamples() {
    const [selectedAllergens, setSelectedAllergens] = useState([
        "Milk",
        "Peanut",
    ]);

    return (
        <div className="ui-docs__example-stack">
            <h4>Searchable Multiple Selection</h4>

            <div className="ui-docs__example-row">
                <div style={{ width: "100%", maxWidth: "420px" }}>
                    <MultiSelect
                        label="Exclude allergens"
                        placeholder="Select allergens..."
                        options={allergenOptions}
                        value={selectedAllergens}
                        onChange={setSelectedAllergens}
                    />
                </div>
            </div>

            <p>
                Selected allergens:{" "}
                {selectedAllergens.length > 0
                    ? selectedAllergens.join(", ")
                    : "None"}
            </p>

            <h4>Disabled State</h4>

            <div className="ui-docs__example-row">
                <div style={{ width: "100%", maxWidth: "420px" }}>
                    <MultiSelect
                        label="Unavailable options"
                        placeholder="Selection disabled"
                        options={allergenOptions}
                        value={[]}
                        onChange={() => { }}
                        disabled
                    />
                </div>
            </div>
        </div>
    );
}

export default MultiSelectExamples;
