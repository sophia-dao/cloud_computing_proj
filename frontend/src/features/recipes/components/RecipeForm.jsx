import { useState } from "react";
import { Link } from "react-router-dom";

import Button from "../../../components/common/Button/Button";
import FormCard from "../../../components/common/FormCard/FormCard";
import Input from "../../../components/common/Input/Input";
import MultiSelect from "../../../components/common/MultiSelect/MultiSelect";
import TextArea from "../../../components/common/TextArea/TextArea";
import IngredientPicker from "../../ingredients/components/IngredientPicker";
import { isAuthError, parseApiError } from "../../../utils/apiErrors";
import useDuplicateNameCheck from "../hooks/useDuplicateNameCheck";
import {
    EMPTY_RECIPE,
    MAX_NAME_LENGTH,
    imageError,
    newIngredientRow,
    serverFieldErrors,
    toRecipePayload,
    validateRecipe,
} from "../recipeForm";
import RecipeIngredientRows from "./RecipeIngredientRows";

import "./RecipeForm.css";

const TAG_TYPE_LABELS = {
    CUISINE: "Cuisine",
    DIET: "Diet",
    COST: "Cost",
    OTHER: "Other",
};

function tagOptions(tags) {
    return tags.map((tag) => ({
        value: tag.id,
        label: `${tag.name} (${TAG_TYPE_LABELS[tag.type] || tag.type})`,
    }));
}

/**
 * Add Recipe form (Issue #67). Owns the form state and checks; the page
 * passes `onSubmit(payload, imageFile)`, which saves and navigates away.
 * If onSubmit throws, the server's errors are shown on the matching fields.
 */
export default function RecipeForm({ tags = [], initialName = "", onSubmit }) {
    const [values, setValues] = useState(() => ({ ...EMPTY_RECIPE, name: initialName }));
    const [errors, setErrors] = useState({});
    const [formError, setFormError] = useState("");
    const [saving, setSaving] = useState(false);
    const [fileInputKey, setFileInputKey] = useState(0);

    const duplicates = useDuplicateNameCheck(values.name);

    function setField(field, value) {
        setValues((current) => ({ ...current, [field]: value }));
    }

    function addIngredient(ingredient) {
        setValues((current) =>
            current.ingredients.some((row) => row.id === ingredient.id)
                ? current
                : { ...current, ingredients: [...current.ingredients, newIngredientRow(ingredient)] }
        );
    }

    function removeIngredient(id) {
        setValues((current) => ({
            ...current,
            ingredients: current.ingredients.filter((row) => row.id !== id),
        }));
    }

    function updateIngredient(id, field, value) {
        setValues((current) => ({
            ...current,
            ingredients: current.ingredients.map((row) =>
                row.id === id ? { ...row, [field]: value } : row
            ),
        }));
    }

    function chooseImage(event) {
        const file = event.target.files?.[0] ?? null;
        setField("image", file);
        setErrors((current) => ({ ...current, image: imageError(file) }));
    }

    function clearImage() {
        setField("image", null);
        setErrors((current) => ({ ...current, image: "" }));
        setFileInputKey((key) => key + 1);
    }

    async function handleSubmit(event) {
        event.preventDefault();

        const found = validateRecipe(values);
        setErrors(found);
        if (Object.keys(found).length > 0) {
            setFormError("Please fix the highlighted fields.");
            return;
        }

        setFormError("");
        setSaving(true);

        try {
            await onSubmit(toRecipePayload(values), values.image);
        } catch (error) {
            if (error?.name === "AbortError") return;

            setErrors(serverFieldErrors(error?.data));
            setFormError(
                isAuthError(error)
                    ? "Your session has expired. Please sign in again."
                    : parseApiError(error).message
            );
            setSaving(false);
        }
    }

    const rowErrors = errors.ingredient_rows || {};

    return (
        <FormCard
            className="recipe-form"
            title="Recipe details"
            description="Fields marked * are required."
            onSubmit={handleSubmit}
            noValidate
            footer={
                <div className="recipe-form__footer">
                    {formError && (
                        <p className="recipe-form__error" role="alert">
                            {formError}
                        </p>
                    )}
                    <Button type="submit" disabled={saving}>
                        {saving ? "Saving..." : "Add recipe"}
                    </Button>
                </div>
            }
        >
            <div className="recipe-form__section">
                <Input
                    label="Recipe name"
                    required
                    maxLength={MAX_NAME_LENGTH}
                    value={values.name}
                    disabled={saving}
                    error={errors.name}
                    onChange={(event) => setField("name", event.target.value)}
                />

                {duplicates.length > 0 && (
                    <div className="recipe-form__duplicate" role="status">
                        <p>
                            <strong>
                                {duplicates.length === 1
                                    ? "A recipe with this name already exists:"
                                    : "Recipes with this name already exist:"}
                            </strong>
                        </p>
                        <ul>
                            {duplicates.map((match) => (
                                <li key={match.id}>
                                    <Link to={`/recipes/${match.id}`} target="_blank" rel="noreferrer">
                                        {match.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                        <p>Check it isn&apos;t the same dish. You can still add yours if it&apos;s different.</p>
                    </div>
                )}

                <TextArea
                    label="Description"
                    rows={3}
                    value={values.description}
                    disabled={saving}
                    error={errors.description}
                    helperText="A sentence or two about the dish."
                    onChange={(event) => setField("description", event.target.value)}
                />

                <div className="recipe-form__times">
                    <Input
                        label="Prep time (minutes)"
                        type="number"
                        inputMode="numeric"
                        min="0"
                        step="1"
                        value={values.preparationTime}
                        disabled={saving}
                        error={errors.preparation_time}
                        onChange={(event) => setField("preparationTime", event.target.value)}
                    />
                    <Input
                        label="Cook time (minutes)"
                        type="number"
                        inputMode="numeric"
                        min="0"
                        step="1"
                        value={values.cookingTime}
                        disabled={saving}
                        error={errors.cooking_time}
                        onChange={(event) => setField("cookingTime", event.target.value)}
                    />
                </div>
            </div>

            <div className="recipe-form__section">
                <IngredientPicker
                    label="Ingredients *"
                    placeholder="Search ingredients to add, e.g. rice"
                    selected={values.ingredients}
                    onAdd={addIngredient}
                    onRemove={removeIngredient}
                    disabled={saving}
                />

                <RecipeIngredientRows
                    rows={values.ingredients}
                    rowErrors={rowErrors}
                    onChange={updateIngredient}
                    onRemove={removeIngredient}
                    disabled={saving}
                />

                {errors.ingredients && (
                    <p className="recipe-form__error" role="alert">
                        {errors.ingredients}
                    </p>
                )}
            </div>

            <div className="recipe-form__section">
                <TextArea
                    label="Instructions"
                    required
                    rows={8}
                    value={values.instructions}
                    disabled={saving}
                    error={errors.instructions}
                    helperText="One step per line works well."
                    onChange={(event) => setField("instructions", event.target.value)}
                />
            </div>

            <div className="recipe-form__section">
                <MultiSelect
                    label="Tags"
                    placeholder="Cuisine, diet, cost..."
                    options={tagOptions(tags)}
                    value={values.tagIds}
                    disabled={saving}
                    onChange={(tagIds) => setField("tagIds", tagIds)}
                />
                {errors.tag_ids && (
                    <p className="recipe-form__error" role="alert">
                        {errors.tag_ids}
                    </p>
                )}

                <div className="recipe-form__photo">
                    <label className="ui-input-field__label" htmlFor="recipe-form-photo">
                        Photo
                    </label>
                    <input
                        key={fileInputKey}
                        id="recipe-form-photo"
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        disabled={saving}
                        aria-describedby="recipe-form-photo-help"
                        onChange={chooseImage}
                    />
                    <span id="recipe-form-photo-help" className="ui-input-field__helper">
                        JPEG, PNG or WebP, up to 5 MB.
                    </span>
                    {values.image && !errors.image && (
                        <Button variant="ghost" size="sm" onClick={clearImage} disabled={saving}>
                            Remove photo
                        </Button>
                    )}
                    {errors.image && (
                        <p className="recipe-form__error" role="alert">
                            {errors.image}
                        </p>
                    )}
                </div>
            </div>
        </FormCard>
    );
}
