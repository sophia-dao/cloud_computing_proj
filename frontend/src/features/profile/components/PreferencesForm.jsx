import { useState } from "react";

import FormCard from "../../../components/common/FormCard/FormCard";
import useSaveState from "../hooks/useSaveState";
import OptionGroup from "./OptionGroup";
import SectionFooter from "./SectionFooter";

const TYPE_ORDER = ["DIET", "CUISINE", "COST", "OTHER"];
const TYPE_LABELS = {
    DIET: "Dietary",
    CUISINE: "Cuisine",
    COST: "Cost",
    OTHER: "Other",
};

function groupTagsByType(tags) {
    const groups = new Map();

    for (const tag of tags) {
        if (!groups.has(tag.type)) groups.set(tag.type, []);
        groups.get(tag.type).push(tag);
    }

    const known = TYPE_ORDER.filter((type) => groups.has(type));
    const unknown = [...groups.keys()].filter((t) => !TYPE_ORDER.includes(t));

    return [...known, ...unknown].map((type) => ({
        type,
        label: TYPE_LABELS[type] || type,
        tags: groups.get(type),
    }));
}

const sameSelection = (a, b) =>
    a.length === b.length && a.every((id) => b.includes(id));

export default function PreferencesForm({ tags, savedIds, onSave }) {
    const [selected, setSelected] = useState(savedIds);
    const save = useSaveState();

    const dirty = !sameSelection(selected, savedIds);
    const groups = groupTagsByType(tags);

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
        save.run(() => onSave(selected), "Preferences saved.");
    }

    return (
        <FormCard
            title="Preferences"
            description="Choose the diets and cuisines you like. They shape your recipe recommendations."
            onSubmit={handleSubmit}
            footer={
                <SectionFooter
                    label="Save preferences"
                    dirty={dirty}
                    saving={save.saving}
                    error={
                        save.status === "error"
                            ? save.fieldErrors.tag_ids || save.message
                            : ""
                    }
                />
            }
        >
            {groups.length === 0 && (
                <p className="profile-settings__empty">
                    No preference tags are available yet.
                </p>
            )}

            {groups.map((group) => (
                <OptionGroup
                    key={group.type}
                    legend={group.label}
                    options={group.tags}
                    selectedIds={selected}
                    onToggle={toggle}
                    disabled={save.saving}
                />
            ))}
        </FormCard>
    );
}
