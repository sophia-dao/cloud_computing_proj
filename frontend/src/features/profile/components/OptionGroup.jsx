import Checkbox from "../../../components/common/Checkbox/Checkbox";

/**
 * A labelled group of checkboxes for options shaped like { id, name }.
 * Used for both Tag preferences and allergens.
 */
export default function OptionGroup({
    legend,
    options,
    selectedIds,
    onToggle,
    disabled = false,
}) {
    if (options.length === 0) return null;

    return (
        <fieldset className="profile-settings__group" disabled={disabled}>
            <legend className="profile-settings__legend">{legend}</legend>

            <div className="profile-settings__options">
                {options.map((option) => (
                    <Checkbox
                        key={option.id}
                        label={option.name}
                        checked={selectedIds.includes(option.id)}
                        onChange={() => onToggle(option.id)}
                    />
                ))}
            </div>
        </fieldset>
    );
}
