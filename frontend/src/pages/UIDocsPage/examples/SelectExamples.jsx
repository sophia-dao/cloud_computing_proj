
import { useState } from "react";

import Select from "../../../components/common/Select/Select";

const cuisineOptions = [
    { label: "Vietnamese", value: "vietnamese" },
    { label: "Italian", value: "italian" },
    { label: "Japanese", value: "japanese" },
];

function SelectExamples() {
    const [cuisine, setCuisine] = useState("");

    return (
        <div className="ui-docs__example-fields">
            <Select
                label="Cuisine"
                placeholder="Choose a cuisine"
                options={cuisineOptions}
                value={cuisine}
                onChange={(event) => setCuisine(event.target.value)}
                helperText="Select your preferred cuisine."
            />

            <Select
                label="Required Selection"
                placeholder="Choose an option"
                options={cuisineOptions}
                defaultValue=""
                required
            />

            <Select
                label="Disabled Selection"
                options={cuisineOptions}
                defaultValue=""
                disabled
            />
        </div>
    );
}

export default SelectExamples;
