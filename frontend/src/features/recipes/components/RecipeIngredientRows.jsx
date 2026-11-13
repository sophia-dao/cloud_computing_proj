import Button from "../../../components/common/Button/Button";
import Checkbox from "../../../components/common/Checkbox/Checkbox";
import Input from "../../../components/common/Input/Input";

/**
 * One row per chosen ingredient: amount, unit and whether it's optional.
 * Ingredients are added with the IngredientPicker above this list.
 */
export default function RecipeIngredientRows({
    rows,
    rowErrors = {},
    onChange,
    onRemove,
    disabled = false,
}) {
    if (rows.length === 0) return null;

    return (
        <ul className="recipe-ingredients" aria-label="Recipe ingredients">
            {rows.map((row, index) => (
                <li key={row.id} className="recipe-ingredients__row">
                    <span className="recipe-ingredients__name">{row.name}</span>

                    <Input
                        label="Amount"
                        type="number"
                        inputMode="decimal"
                        min="0"
                        step="any"
                        placeholder="e.g. 2"
                        value={row.quantity}
                        disabled={disabled}
                        aria-label={`Amount of ${row.name}`}
                        onChange={(event) => onChange(row.id, "quantity", event.target.value)}
                    />

                    <Input
                        label="Unit"
                        placeholder="e.g. cup"
                        maxLength={32}
                        value={row.unit}
                        disabled={disabled}
                        aria-label={`Unit for ${row.name}`}
                        onChange={(event) => onChange(row.id, "unit", event.target.value)}
                    />

                    <Checkbox
                        label="Optional"
                        checked={row.isOptional}
                        disabled={disabled}
                        aria-label={`${row.name} is optional`}
                        onChange={(event) => onChange(row.id, "isOptional", event.target.checked)}
                    />

                    <Button
                        variant="ghost"
                        size="sm"
                        disabled={disabled}
                        aria-label={`Remove ${row.name}`}
                        onClick={() => onRemove(row.id)}
                    >
                        Remove
                    </Button>

                    {rowErrors[index] && (
                        <p className="recipe-ingredients__error" role="alert">
                            {rowErrors[index]}
                        </p>
                    )}
                </li>
            ))}
        </ul>
    );
}
