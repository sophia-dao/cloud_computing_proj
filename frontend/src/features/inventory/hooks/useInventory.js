import { useCallback, useEffect, useState } from "react";

import { useToast } from "../../../hooks/useToast";
import inventoryService from "../../../services/inventoryService";
import { parseApiError } from "../../../utils/apiErrors";

const byName = (a, b) => a.ingredient.name.localeCompare(b.ingredient.name);

/**
 * Loads the signed-in user's saved ingredients and exposes add / remove.
 * The list always reflects what the server confirmed; failures show a toast
 * and leave the list unchanged.
 */
export default function useInventory() {
    const { showToast } = useToast();

    const [status, setStatus] = useState("loading"); // loading | ready | error
    const [items, setItems] = useState([]);
    const [loadError, setLoadError] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    const [pendingAdds, setPendingAdds] = useState([]); // ingredient ids
    const [pendingRemovals, setPendingRemovals] = useState([]); // item ids

    useEffect(() => {
        const controller = new AbortController();

        inventoryService
            .getItems({ signal: controller.signal })
            .then((list) => {
                if (controller.signal.aborted) return;

                setItems([...list].sort(byName));
                setStatus("ready");
            })
            .catch((error) => {
                if (controller.signal.aborted || error?.name === "AbortError") {
                    return;
                }

                setLoadError(parseApiError(error));
                setStatus("error");
            });

        return () => controller.abort();
    }, [reloadKey]);

    const reload = useCallback(() => {
        setStatus("loading");
        setLoadError(null);
        setReloadKey((key) => key + 1);
    }, []);

    const addIngredient = useCallback(
        async (ingredient) => {
            setPendingAdds((ids) => [...ids, ingredient.id]);

            try {
                const item = await inventoryService.addItem(ingredient.id);

                setItems((current) =>
                    current.some((existing) => existing.id === item.id)
                        ? current
                        : [...current, item].sort(byName)
                );
            } catch (error) {
                showToast({
                    type: "error",
                    message: `Couldn't add ${ingredient.name}. ${
                        parseApiError(error).message
                    }`,
                });
            } finally {
                setPendingAdds((ids) => ids.filter((id) => id !== ingredient.id));
            }
        },
        [showToast]
    );

    const removeItem = useCallback(
        async (item) => {
            setPendingRemovals((ids) => [...ids, item.id]);

            try {
                await inventoryService.removeItem(item.id);

                setItems((current) =>
                    current.filter((existing) => existing.id !== item.id)
                );
            } catch (error) {
                if (error?.status === 404) {
                    // Already removed (e.g. in another tab): the list is
                    // now correct once it's gone locally too.
                    setItems((current) =>
                        current.filter((existing) => existing.id !== item.id)
                    );
                } else {
                    showToast({
                        type: "error",
                        message: `Couldn't remove ${item.ingredient.name}. ${
                            parseApiError(error).message
                        }`,
                    });
                }
            } finally {
                setPendingRemovals((ids) => ids.filter((id) => id !== item.id));
            }
        },
        [showToast]
    );

    return {
        status,
        items,
        loadError,
        reload,
        pendingAdds,
        pendingRemovals,
        addIngredient,
        removeItem,
    };
}
