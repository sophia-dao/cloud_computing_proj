
import ButtonExamples from "./examples/ButtonExamples";
import InputExamples from "./examples/InputExamples";
import SelectExamples from "./examples/SelectExamples";
import FormCardExamples from "./examples/FormCardExamples";
import CardExamples from "./examples/CardExamples";

export const docsRegistry = [
    {
        id: "button",
        name: "Button",
        description:
            "Reusable button with variants, sizes, and loading states.",
        file: "src/components/common/Button/Button.jsx",
        Preview: ButtonExamples,
        props: [
            ["variant", "string", '"primary"', "primary, secondary, accent, ghost"],
            ["size", "string", '"md"', "sm, md, lg"],
            ["type", "string", '"button"', "Native button type"],
            ["disabled", "boolean", "false", "Disable interaction"],
            ["loading", "boolean", "false", "Show loading state"],
            ["children", "ReactNode", "—", "Button content"],
        ],
        code: `import Button from "../../components/common/Button/Button";

<Button variant="primary" size="md">
  Save Recipe
</Button>

<Button variant="secondary">
  Cancel
</Button>`,
    },
    {
        id: "input",
        name: "Input",
        description:
            "Reusable text input with labels, helper text, and errors.",
        file: "src/components/common/Input/Input.jsx",
        Preview: InputExamples,
        props: [
            ["label", "string", "—", "Field label"],
            ["type", "string", '"text"', "HTML input type"],
            ["placeholder", "string", "—", "Placeholder text"],
            ["required", "boolean", "false", "Mark field as required"],
            ["disabled", "boolean", "false", "Disable field"],
            ["error", "string", "—", "Validation error message"],
            ["helperText", "string", "—", "Additional guidance"],
        ],
        code: `import Input from "../../components/common/Input/Input";

<Input
  label="Ingredient"
  name="ingredient"
  placeholder="e.g. Chicken"
  required
/>`,
    },
    {
        id: "select",
        name: "Select",
        description:
            "Reusable dropdown field with configurable options.",
        file: "src/components/common/Select/Select.jsx",
        Preview: SelectExamples,
        props: [
            ["label", "string", "—", "Field label"],
            ["options", "array", "[]", "Objects with label and value"],
            ["placeholder", "string", '"Select an option"', "Default prompt"],
            ["required", "boolean", "false", "Require a selection"],
            ["disabled", "boolean", "false", "Disable dropdown"],
            ["error", "string", "—", "Validation error"],
            ["helperText", "string", "—", "Additional guidance"],
        ],
        code: `import Select from "../../components/common/Select/Select";

<Select
  label="Cuisine"
  name="cuisine"
  defaultValue=""
  options={[
    { label: "Vietnamese", value: "vietnamese" },
    { label: "Italian", value: "italian" },
  ]}
/>`,
    },
    {
        id: "form-card",
        name: "FormCard",
        description:
            "Reusable form container with responsive columns, borders, and shadows.",
        file: "src/components/common/FormCard/FormCard.jsx",
        Preview: FormCardExamples,
        props: [
            ["title", "string", "—", "Form heading"],
            ["description", "string", "—", "Supporting text"],
            ["columns", "number", "1", "Desktop column count"],
            ["bordered", "boolean", "true", "Show outer border"],
            ["floating", "boolean", "false", "Apply floating shadow"],
            ["footer", "ReactNode", "—", "Form action area"],
            ["onSubmit", "function", "—", "Form submission handler"],
            ["children", "ReactNode", "—", "Form fields"],
        ],
        code: `import FormCard from "../../components/common/FormCard/FormCard";
import Input from "../../components/common/Input/Input";
import Button from "../../components/common/Button/Button";

<FormCard
  title="Recipe Search"
  columns={2}
  bordered
  floating
  onSubmit={handleSubmit}
  footer={<Button type="submit">Search</Button>}
>
  <Input label="Ingredient" required />
  <Input label="Maximum Time" type="number" />
</FormCard>`,
    },

    {
        id: "card",
        name: "Card",
        description:
            "Reusable content container with optional image, border, shadow, and footer.",
        file: "src/components/common/Card/Card.jsx",
        Preview: CardExamples,
        props: [
            ["title", "string", "—", "Card heading"],
            ["description", "string", "—", "Supporting text"],
            ["children", "ReactNode", "—", "Main card content"],
            ["footer", "ReactNode", "—", "Optional footer content"],
            ["image", "string", "—", "Image URL"],
            ["imageAlt", "string", '""', "Image alternative text"],
            ["bordered", "boolean", "true", "Show outer border"],
            ["floating", "boolean", "false", "Apply floating shadow"],
            ["padding", "boolean", "true", "Enable internal padding"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        code: `import Card from "../../components/common/Card/Card";
import Button from "../../components/common/Button/Button";

<Card
    title="Chicken Fried Rice"
    description="Ready in 25 minutes"
    bordered
    floating
    footer={<Button>View Recipe</Button>}
>
    <p>Ingredients: Rice, chicken, eggs.</p>
</Card>`,
    },

];
