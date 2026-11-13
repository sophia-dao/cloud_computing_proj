import { useState } from "react";

import FormCard from "../../../components/common/FormCard/FormCard";
import useSaveState from "../hooks/useSaveState";
import OptionGroup from "./OptionGroup";
import SectionFooter from "./SectionFooter";

const sameSelection = (a, b) =>
    a.length === b.length && a.every((id) => b.includes(id));

export default function AllergiesForm({ allergens, savedIds, onSave }) {
    const [selected, setSelected] = useState(savedIds);
    const save = useSaveState();

    const dirty = !sameSelection(selected, savedIds);

    function toggle(id) {
        save.reset();
        setSelected((current) =>
            current.includes(id)
                ? current.filter((value) => value !== id)
                : [...current, id]
        );
    }

    function handleSubmit(event) {
        event.preventDefault();
        save.run(() => onSave(selected), "Allergies saved.");
    }

    return (
        <FormCard
            title="Allergies"
            description="Recipes with ingredients linked to these allergens are hidden from your recipe lists. Allergen data is still being verified, so always check each recipe's ingredients."
            onSubmit={handleSubmit}
            footer={
                <SectionFooter
                    label="Save allergies"
                    dirty={dirty}
                    saving={save.saving}
                    error={
                        save.status === "error"
                            ? save.fieldErrors.allergen_ids || save.message
                            : ""
                    }
                />
            }
        >
            {allergens.length === 0 && (
                <p className="profile-settings__empty">
                    No allergens are available yet.
                </p>
            )}

            <OptionGroup
                legend="Allergens"
                options={allergens}
                selectedIds={selected}
                onToggle={toggle}
                disabled={save.saving}
            />
        </FormCard>
    );
}
