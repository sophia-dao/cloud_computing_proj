import { useCallback, useMemo, useState } from "react";

/**
 * Temporary (in-memory) selection of canonical ingredients.
 * Guest selections intentionally live only in frontend state and are
 * never written to persistent inventory.
 */
export default function useIngredientSelection(initial = []) {
    const [selected, setSelected] = useState(() => dedupe(initial));

    const add = useCallback((ingredient) => {
        if (ingredient?.id == null) return;

        setSelected((current) =>
            current.some((item) => item.id === ingredient.id)
                ? current
                : [...current, { id: ingredient.id, name: ingredient.name, category: ingredient.category }]
        );
    }, []);

    const remove = useCallback((id) => {
        setSelected((current) => current.filter((item) => item.id !== id));
    }, []);

    const clear = useCallback(() => setSelected([]), []);

    const selectedIds = useMemo(
        () => selected.map((item) => item.id),
        [selected]
    );

    const isSelected = useCallback(
        (id) => selectedIds.includes(id),
        [selectedIds]
    );

    return { selected, selectedIds, add, remove, clear, isSelected };
}

function dedupe(items) {
    const seen = new Set();

    return items.filter((item) => {
        if (item?.id == null || seen.has(item.id)) return false;
        seen.add(item.id);
        return true;
    });
}
