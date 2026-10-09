
import ButtonExamples from "./examples/ButtonExamples";
import InputExamples from "./examples/InputExamples";
import SelectExamples from "./examples/SelectExamples";
import FormCardExamples from "./examples/FormCardExamples";
import CardExamples from "./examples/CardExamples";
import ModalExamples from "./examples/ModalExamples";
import ToastExamples from "./examples/ToastExamples";
import SearchBarExamples from "./examples/SearchBarExamples";
import BadgeExamples from "./examples/BadgeExamples";
import SwitchExamples from "./examples/SwitchExamples";
import CheckboxExamples from "./examples/CheckboxExamples";
import SpinnerExamples from "./examples/SpinnerExamples";
import ErrorStateExamples from "./examples/ErrorStateExamples";
import EmptyStateExamples from "./examples/EmptyState";

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

{
        id: "badge",
        name: "Badge / Tag",
        description:
            "Compact labels for categories, statuses, and removable selections.",
        file: "src/components/common/Badge/Badge.jsx",
        Preview: BadgeExamples,
        props: [
            ["children", "ReactNode", "—", "Badge label or content"],
            ["variant", "string", '"neutral"', "neutral, success, warning, danger, accent"],
            ["size", "string", '"md"', "sm, md"],
            ["removable", "boolean", "false", "Show remove button"],
            ["onRemove", "function", "—", "Callback when remove is clicked"],
            ["disabled", "boolean", "false", "Disable removal"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "Badge is a compact reusable component for displaying short labels, " +
            "statuses, and categories. It can also function as a removable tag " +
            "for selected ingredients or filters. Variants communicate different " +
            "types of information while maintaining consistent styling across " +
            "the application.",
        useCases: [
            "Displaying recipe cuisine and dietary categories.",
            "Showing selected ingredients as removable tags.",
            "Indicating recipe match status.",
            "Highlighting allergens or unavailable ingredients.",
            "Displaying active filters and preferences.",
        ],
        notes: [
            "Use removable={true} only when the user can remove the item.",
            "Provide onRemove when using a removable badge.",
            "Use stable IDs as React keys when rendering lists of tags.",
            "Do not rely on badge color alone to communicate important information.",
            "Badge is a display component; it does not automatically update application state.",
        ],
        code: `import Badge from "../../components/common/Badge/Badge";

function RecipeTags() {
    return (
        <div>
            <Badge variant="accent">Vietnamese</Badge>
            <Badge variant="success">Vegetarian</Badge>
            <Badge variant="warning">Partial Match</Badge>
        </div>
    );
}`,
    },

{
        id: "checkbox",
        name: "Checkbox",
        description:
            "Reusable checkbox for selecting independent options, preferences, and filters.",
        file: "src/components/common/Checkbox/Checkbox.jsx",
        Preview: CheckboxExamples,
        props: [
            ["label", "string", "—", "Visible checkbox label"],
            ["description", "string", "—", "Optional supporting text"],
            ["error", "string", "—", "Validation error message"],
            ["checked", "boolean", "—", "Controlled checked state"],
            ["defaultChecked", "boolean", "false", "Initial uncontrolled state"],
            ["onChange", "function", "—", "Native checkbox change event"],
            ["disabled", "boolean", "false", "Disable interaction"],
            ["name", "string", "—", "Form field name"],
            ["required", "boolean", "false", "Require selection"],
            ["id", "string", "Auto-generated", "Input ID"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "Checkbox is a reusable form control for selecting individual " +
            "options or multiple independent choices. It uses a native HTML " +
            "checkbox to provide keyboard support and accessibility. " +
            "It supports controlled and uncontrolled state, optional " +
            "descriptions, validation errors, and disabled behavior.",
        useCases: [
            "Selecting dietary preferences.",
            "Choosing allergy restrictions.",
            "Enabling multiple recipe filters.",
            "Selecting items from a list.",
            "Accepting required terms or conditions.",
        ],
        notes: [
            "Use checked and onChange for controlled checkboxes.",
            "Use defaultChecked for uncontrolled checkboxes.",
            "The onChange callback receives a native React change event.",
            "Use event.target.checked to read the boolean value.",
            "Checkbox is appropriate for multiple independent selections.",
            "Use Switch instead for immediate on/off settings.",
        ],
        code: `import { useState } from "react";
import Checkbox from "../../components/common/Checkbox/Checkbox";

function Example() {
    const [vegetarian, setVegetarian] = useState(false);

    return (
        <Checkbox
            label="Vegetarian"
            checked={vegetarian}
            onChange={(event) =>
                setVegetarian(event.target.checked)
            }
        />
    );
}`,
    },

{
        id: "switch",
        name: "Switch",
        description:
            "Reusable toggle control for enabling or disabling application settings.",
        file: "src/components/common/Switch/Switch.jsx",
        Preview: SwitchExamples,
        props: [
            ["label", "string", "—", "Visible setting label"],
            ["description", "string", "—", "Optional supporting text"],
            ["checked", "boolean", "—", "Controlled on/off state"],
            ["defaultChecked", "boolean", "false", "Initial uncontrolled state"],
            ["onChange", "function", "—", "Native checkbox change event"],
            ["disabled", "boolean", "false", "Disable interaction"],
            ["name", "string", "—", "Form field name"],
            ["id", "string", "Auto-generated", "Input ID"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "Switch is a reusable toggle control for binary application " +
            "settings. It uses a native checkbox with role='switch' " +
            "to provide accessible keyboard interaction and checked state. " +
            "The component supports controlled and uncontrolled usage, " +
            "optional descriptions, and disabled behavior.",
        useCases: [
            "Enabling or disabling notifications.",
            "Automatically applying saved recipe preferences.",
            "Toggling optional application features.",
            "Controlling binary profile settings.",
        ],
        notes: [
            "Use Switch for on/off settings rather than selecting multiple options.",
            "Use checked and onChange for controlled state.",
            "Read event.target.checked to determine whether the switch is enabled.",
            "The parent component is responsible for persisting setting changes.",
            "Use Checkbox for selections that are submitted as part of a form.",
        ],
        code: `import { useState } from "react";
import Switch from "../../components/common/Switch/Switch";

function Example() {
    const [enabled, setEnabled] = useState(false);

    return (
        <Switch
            label="Apply Saved Preferences"
            checked={enabled}
            onChange={(event) =>
                setEnabled(event.target.checked)
            }
        />
    );
}`,
    },

{
        id: "spinner",
        name: "Spinner",
        description:
            "Accessible animated loading indicator with configurable sizes.",
        file: "src/components/common/Spinner/Spinner.jsx",
        Preview: SpinnerExamples,
        props: [
            ["size", "string", '"md"', "sm, md, lg"],
            ["label", "string", '"Loading..."', "Accessible loading message"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "Spinner provides visual feedback while an asynchronous operation " +
            "is running. It supports three sizes and an accessible loading label. " +
            "It does not perform any API requests or manage loading state.",
        useCases: [
            "Loading recipe recommendations.",
            "Searching ingredients.",
            "Fetching inventory data.",
            "Loading user profile information.",
        ],
        notes: [
            "Use size='sm' for inline loading indicators.",
            "Use size='lg' for larger loading sections.",
            "The parent component controls when Spinner appears.",
            "Provide a descriptive label when the loading operation is specific.",
        ],
        code: `import Spinner from "../../components/common/Spinner/Spinner";

function Example() {
    return <Spinner size="md" label="Loading recipes..." />;
}`,
    },
    {
        id: "empty-state",
        name: "EmptyState",
        description:
            "Reusable placeholder for empty results, collections, and pages.",
        file: "src/components/common/EmptyState/EmptyState.jsx",
        Preview: EmptyStateExamples,
        props: [
            ["title", "string", '"Nothing here yet"', "Main message"],
            ["description", "string", '"There is no content to display."', "Supporting text"],
            ["icon", "ReactNode", '"📭"', "Decorative icon"],
            ["action", "ReactNode", "—", "Optional action button or link"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "EmptyState communicates that a request succeeded but no matching " +
            "content is available. It provides a clear explanation and can " +
            "offer an action that helps users continue.",
        useCases: [
            "No matching recipe recommendations.",
            "Empty saved recipe lists.",
            "No ingredients in inventory.",
            "No search results.",
        ],
        notes: [
            "Use EmptyState only when the data is successfully loaded but empty.",
            "Use ErrorState when an API request fails.",
            "Use action to provide a meaningful next step.",
            "Avoid technical error messages in empty states.",
        ],
        code: `import EmptyState from "../../components/common/EmptyState/EmptyState";

function Example() {
    return (
        <EmptyState
            title="No Recipes Found"
            description="Try adjusting your search filters."
        />
    );
}`,
    },
    {
        id: "error-state",
        name: "ErrorState",
        description:
            "Reusable error message with optional retry action.",
        file: "src/components/common/ErrorState/ErrorState.jsx",
        Preview: ErrorStateExamples,
        props: [
            ["title", "string", '"Something went wrong"', "Error heading"],
            ["description", "string", "Default error message", "Error explanation"],
            ["onRetry", "function", "—", "Retry callback"],
            ["retryLabel", "string", '"Try Again"', "Retry button text"],
            ["className", "string", '""', "Additional CSS class"],
        ],
        details:
            "ErrorState provides consistent feedback when an operation fails. " +
            "It can display a user-friendly explanation and optionally provide " +
            "a retry action. The parent component remains responsible for " +
            "performing the retry operation.",
        useCases: [
            "Failed recipe API requests.",
            "Inventory loading errors.",
            "Backend connection failures.",
            "Profile data retrieval failures.",
        ],
        notes: [
            "Use ErrorState for failed operations, not empty results.",
            "Provide onRetry only when retrying is meaningful.",
            "Avoid exposing raw server errors or sensitive information.",
            "The parent component manages loading and error state.",
        ],
        code: `import ErrorState from "../../components/common/ErrorState/ErrorState";

function Example() {
    return (
        <ErrorState
            title="Unable to Load Recipes"
            onRetry={() => console.log("Retry requested")}
        />
    );
}`,
    },

];
