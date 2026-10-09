
import Input from "../../../components/common/Input/Input";

function InputExamples() {
    return (
        <div className="ui-docs__example-fields">
            <Input
                label="Ingredient"
                placeholder="e.g. Chicken"
                helperText="Enter an ingredient name."
            />

            <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                required
            />

            <Input
                label="Invalid Input"
                defaultValue="Invalid value"
                error="Please enter a valid value."
            />

            <Input
                label="Disabled Input"
                placeholder="Unavailable"
                disabled
            />
        </div>
    );
}

export default InputExamples;
