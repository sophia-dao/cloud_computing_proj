
import ButtonExamples from "./examples/ButtonExamples";
import InputExamples from "./examples/InputExamples";
import SelectExamples from "./examples/SelectExamples";
import FormCardExamples from "./examples/FormCardExamples";
import CardExamples from "./examples/CardExamples";
import ModalExamples from "./examples/ModalExamples";

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

        details:
            "FormCard provides a reusable HTML form container with a structured " +
            "header, responsive field grid, and optional footer. It is designed " +
            "to work with shared field components such as Input and Select. " +
            "Developers can configure the number of desktop columns and independently " +
            "enable or disable borders and floating shadows.",

        useCases: [
            "Creating recipe search and filtering forms.",
            "Updating user profiles and preferences.",
            "Adding or editing inventory information.",
            "Collecting ingredient information.",
            "Building account settings forms.",
        ],

        notes: [
            "FormCard renders a real HTML form element.",
            "Use onSubmit to handle form submissions and prevent page reloads when appropriate.",
            "Use columns to configure the desktop grid; fields stack on mobile.",
            "The parent component manages input values, validation, and API requests.",
            "Use type='submit' on the footer button when it should submit the form.",
            "Avoid nesting FormCard inside another HTML form.",
            "Use Card for general content that does not require form submission.",
        ],

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

        details:
            "Card is a reusable presentation container designed to group related " +
            "information into a consistent visual section. It supports an optional " +
            "image, title, description, body content, and footer. Borders and shadows " +
            "are controlled independently, allowing different visual styles without " +
            "creating separate components.",

        useCases: [
            "Displaying recipe previews and recipe details.",
            "Showing saved recipes or favorite items.",
            "Organizing dashboard widgets and statistics.",
            "Displaying inventory summaries.",
            "Grouping related read-only information.",
        ],

        notes: [
            "Use FormCard instead when the primary purpose is collecting form input.",
            "The image prop accepts an image URL; provide meaningful imageAlt text for informative images.",
            "The footer accepts any React content, including buttons and links.",
            "Setting padding={false} removes padding from the body and footer, but does not change the image area.",
            "Card does not automatically implement navigation or click behavior.",
        ],

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

{
        id: "modal",
        name: "Modal",

        details:
            "Modal is a reusable overlay dialog built with the native HTML dialog " +
            "element. It allows users to complete focused tasks without leaving " +
            "the current page. It supports configurable sizes, headings, descriptions, " +
            "custom body content, and footer actions. The parent component controls " +
            "visibility using the open prop and responds to close requests through " +
            "the onClose callback.",

        useCases: [
            "Confirming deletion of inventory items.",
            "Displaying important warnings or confirmations.",
            "Editing a small amount of information.",
            "Showing additional recipe details.",
            "Requesting confirmation before irreversible actions.",
        ],

        notes: [
            "The parent must update open when onClose is called.",
            "The dialog supports Escape-key closing.",
            "Backdrop closing can be disabled with closeOnBackdrop={false}.",
            "Use size='sm', 'md', or 'lg' to control maximum width.",
            "Modal content can include Input, Select, and other reusable components.",
            "Do not use a modal for large, complex workflows that would work better as dedicated pages.",
            "Avoid nesting multiple modal dialogs unless absolutely necessary.",
        ],

        file: "src/components/common/Modal/Modal.jsx",
        Preview: ModalExamples,
        props: [
            ["open", "boolean", "false", "Whether the modal is open"],
            ["onClose", "function", "—", "Callback requesting closure"],
            ["title", "string", "—", "Dialog heading"],
            ["description", "string", "—", "Supporting text"],
            ["children", "ReactNode", "—", "Modal body"],
            ["footer", "ReactNode", "—", "Footer actions"],
            ["size", "string", '"md"', "sm, md, lg"],
            ["closeOnBackdrop", "boolean", "true", "Allow backdrop closing"],
            ["showCloseButton", "boolean", "true", "Show close button"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        code: `import { useState } from "react";
import Modal from "../../components/common/Modal/Modal";
import Button from "../../components/common/Button/Button";

function Example() {
    const [open, setOpen] = useState(false);

    return (
        <>
            <Button onClick={() => setOpen(true)}>
                Open Modal
            </Button>

            <Modal
                open={open}
                onClose={() => setOpen(false)}
                title="Confirm Action"
                footer={
                    <Button onClick={() => setOpen(false)}>
                        Close
                    </Button>
                }
            >
                <p>Modal content goes here.</p>
            </Modal>
        </>
    );
}`,
    },
    

];
