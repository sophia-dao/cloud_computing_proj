
import Button from "../../../components/common/Button/Button";
import FormCard from "../../../components/common/FormCard/FormCard";
import Input from "../../../components/common/Input/Input";
import Select from "../../../components/common/Select/Select";

function FormCardExamples() {
    function handleSubmit(event) {
        event.preventDefault();
    }

    return (
        <div className="ui-docs__example-stack">
            <FormCard
                title="Recipe Search"
                description="Example of a two-column form."
                columns={2}
                bordered
                floating
                onSubmit={handleSubmit}
                footer={<Button type="submit">Search</Button>}
            >
                <Input
                    label="Ingredient"
                    placeholder="e.g. Chicken"
                    required
                />

                <Select
                    label="Cuisine"
                    placeholder="Any cuisine"
                    defaultValue=""
                    options={[
                        { label: "Vietnamese", value: "vietnamese" },
                        { label: "Italian", value: "italian" },
                    ]}
                />
            </FormCard>

            <FormCard
                title="Borderless Form"
                description="No border or floating shadow."
                bordered={false}
                floating={false}
                onSubmit={handleSubmit}
            >
                <Input label="Example Field" />
            </FormCard>
        </div>
    );
}

export default FormCardExamples;
