/**
 * Add Recipe form rules (Issue #67): client-side checks that mirror the
 * backend, the request body, and turning server errors back into fields.
 * The backend stays the authority; these checks just give faster feedback.
 */

export const MAX_NAME_LENGTH = 200;
export const MAX_UNIT_LENGTH = 32;
export const MAX_IMAGE_BYTES = 5_000_000;
export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
// RecipeIngredient.quantity is DECIMAL(8, 3).
const MAX_QUANTITY = 99999.999;

export const EMPTY_RECIPE = Object.freeze({
    name: "",
    description: "",
    instructions: "",
    preparationTime: "",
    cookingTime: "",
    ingredients: [], // [{ id, name, quantity, unit, isOptional }]
    tagIds: [],
    image: null,
});

/** "  Kimchi   Fried Rice " -> "Kimchi Fried Rice" (same as the backend). */
export function normalizeRecipeName(name) {
    return String(name ?? "").split(/\s+/).filter(Boolean).join(" ");
}

export function newIngredientRow(ingredient) {
    return {
        id: ingredient.id,
        name: ingredient.name,
        quantity: "",
        unit: "",
        isOptional: false,
    };
}

function minutes(value) {
    const text = String(value ?? "").trim();
    return text === "" ? null : Number(text);
}

function isWholeMinutes(value) {
    return /^\d+$/.test(String(value ?? "").trim());
}

function quantity(value) {
    const text = String(value ?? "").trim();
    return text === "" ? null : Math.round(Number(text) * 1000) / 1000;
}

export function imageError(file) {
    if (!file) return "";
    if (!IMAGE_TYPES.includes(file.type)) return "Choose a JPEG, PNG or WebP image.";
    if (file.size > MAX_IMAGE_BYTES) return "Images must be 5 MB or smaller.";
    return "";
}

/**
 * Errors keyed by API field name, plus `ingredient_rows` ({ index: message })
 * for problems on one ingredient. Empty object means the form can be sent.
 */
export function validateRecipe(values) {
    const errors = {};
    const rowErrors = {};

    if (!normalizeRecipeName(values.name)) {
        errors.name = "Give the recipe a name.";
    } else if (normalizeRecipeName(values.name).length > MAX_NAME_LENGTH) {
        errors.name = `Keep the name to ${MAX_NAME_LENGTH} characters or fewer.`;
    }

    if (!values.instructions.trim()) {
        errors.instructions = "Add the cooking instructions.";
    }

    if (values.ingredients.length === 0) {
        errors.ingredients = "Add at least one ingredient.";
    }

    values.ingredients.forEach((row, index) => {
        const amount = String(row.quantity ?? "").trim();
        if (amount !== "") {
            const value = quantity(amount);
            if (!Number.isFinite(value) || value <= 0) {
                rowErrors[index] = "Amount must be more than zero.";
            } else if (value > MAX_QUANTITY) {
                rowErrors[index] = "That amount is too large.";
            }
        }
        if (row.unit.trim().length > MAX_UNIT_LENGTH) {
            rowErrors[index] = `Keep the unit to ${MAX_UNIT_LENGTH} characters or fewer.`;
        }
    });
    if (Object.keys(rowErrors).length > 0) errors.ingredient_rows = rowErrors;

    for (const [field, key] of [
        ["preparationTime", "preparation_time"],
        ["cookingTime", "cooking_time"],
    ]) {
        const text = String(values[field] ?? "").trim();
        if (text !== "" && !isWholeMinutes(text)) {
            errors[key] = "Use whole minutes, e.g. 15.";
        }
    }

    const photoError = imageError(values.image);
    if (photoError) errors.image = photoError;

    return errors;
}

/** Body for POST /api/recipes/. The image is uploaded separately. */
export function toRecipePayload(values) {
    return {
        name: normalizeRecipeName(values.name),
        description: values.description.trim(),
        instructions: values.instructions.trim(),
        preparation_time: minutes(values.preparationTime),
        cooking_time: minutes(values.cookingTime),
        ingredients: values.ingredients.map((row) => ({
            ingredient_id: row.id,
            quantity: quantity(row.quantity),
            unit: row.unit.trim() || null,
            is_optional: row.isOptional,
        })),
        tag_ids: values.tagIds,
    };
}

function messages(value) {
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return value.flatMap((item) => messages(item) || []).join(" ");
    if (value && typeof value === "object") return messages(Object.values(value));
    return "";
}

/**
 * DRF 400 body -> the same shape validateRecipe returns. Errors on one
 * ingredient come back as a list lined up with the submitted ingredients.
 */
export function serverFieldErrors(data) {
    const errors = {};
    if (!data || typeof data !== "object" || Array.isArray(data)) return errors;

    for (const [key, value] of Object.entries(data)) {
        const perRow =
            key === "ingredients" &&
            Array.isArray(value) &&
            value.some((item) => item && typeof item === "object" && !Array.isArray(item));

        if (perRow) {
            const rows = {};
            value.forEach((item, index) => {
                const text = messages(item);
                if (text) rows[index] = text;
            });
            if (Object.keys(rows).length > 0) errors.ingredient_rows = rows;
        } else {
            const text = messages(value);
            if (text) errors[key] = text;
        }
    }

    return errors;
}
