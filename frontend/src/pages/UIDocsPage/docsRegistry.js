
import ButtonExamples from "./examples/ButtonExamples";
import InputExamples from "./examples/InputExamples";
import SelectExamples from "./examples/SelectExamples";
import FormCardExamples from "./examples/FormCardExamples";
import CardExamples from "./examples/CardExamples";
import ModalExamples from "./examples/ModalExamples";
import ToastExamples from "./examples/ToastExamples";
import SearchBarExamples from "./examples/SearchBarExamples";

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

    {
        id: "toast",
        name: "Toast",
        description:
            "Global, non-blocking notifications for success, errors, warnings, and information.",
        file: "src/components/common/Toast/Toast.jsx",
        Preview: ToastExamples,
        props: [
            ["type", "string", '"info"', "success, error, warning, info"],
            ["message", "string", "—", "Notification message"],
            ["duration", "number", "4000", "Auto-dismiss delay in milliseconds"],
            ["dismissible", "boolean", "true", "Show manual dismiss button"],
        ],
        details:
            "Toast provides temporary, non-blocking feedback about actions " +
            "or system events. Notifications are managed globally by ToastProvider, " +
            "so any component inside the provider can display them using useToast. " +
            "Multiple notifications can be displayed at the same time.",
        useCases: [
            "Confirming that a recipe was saved.",
            "Displaying API request failures.",
            "Informing users that preferences were updated.",
            "Warning about unavailable ingredients.",
        ],
        notes: [
            "Wrap the application with ToastProvider once.",
            "Call showToast from useToast to display a notification.",
            "Use duration={0} for a persistent notification.",
            "Toast should not replace Modal for actions requiring confirmation.",
            "Avoid including sensitive information in notifications.",
        ],
        code: `import { useToast } from "../../hooks/useToast";

function SaveRecipeButton() {
    const { showToast } = useToast();

    function handleSave() {
        showToast({
            type: "success",
            message: "Recipe saved successfully!",
            duration: 4000,
        });
    }

    return <button onClick={handleSave}>Save Recipe</button>;
}`,
    },    

{
        id: "search-bar",
        name: "SearchBar",
        description:
            "Reusable search input with debouncing, loading feedback, and a clear button.",
        file: "src/components/common/SearchBar/SearchBar.jsx",
        Preview: SearchBarExamples,
        props: [
            ["value", "string", "—", "Controlled search value"],
            ["defaultValue", "string", '""', "Initial uncontrolled value"],
            ["onChange", "function", "—", "Called with updated text"],
            ["onSearch", "function", "—", "Called with the search query"],
            ["onClear", "function", "—", "Called when the clear button is clicked"],
            ["placeholder", "string", '"Search..."', "Input placeholder"],
            ["label", "string", '"Search"', "Accessible field label"],
            ["debounce", "number", "300", "Delay in milliseconds"],
            ["loading", "boolean", "false", "Show loading indicator"],
            ["disabled", "boolean", "false", "Disable the input"],
            ["showClear", "boolean", "true", "Show clear button"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "SearchBar is a reusable search input that manages text entry, " +
            "debounced search events, and loading feedback. It supports both " +
            "controlled and uncontrolled values. The component does not " +
            "fetch data itself; feature-specific services handle API requests.",
        useCases: [
            "Searching the canonical Ingredient database.",
            "Searching recipes by name.",
            "Filtering saved recipes.",
            "Searching administrative lists.",
        ],
        notes: [
            "Use onSearch to connect the component to a search function.",
            "Debouncing reduces unnecessary search requests.",
            "Pressing Enter triggers an immediate search.",
            "Use loading to indicate that a request is in progress.",
            "Use controlled mode when search state is shared with filters or other components.",
            "Do not make API requests directly inside SearchBar.",
            "SearchBar renders a form; do not nest it inside another HTML form.",
        ],
        code: `import { useState } from "react";
import SearchBar from "../../components/common/SearchBar/SearchBar";

function IngredientSearch() {
    const [query, setQuery] = useState("");

    function handleSearch(searchTerm) {
        console.log("Search:", searchTerm);
    }

    return (
        <SearchBar
            label="Search Ingredients"
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            placeholder="Search ingredients..."
            debounce={300}
        />
    );
}`,
    },

];
