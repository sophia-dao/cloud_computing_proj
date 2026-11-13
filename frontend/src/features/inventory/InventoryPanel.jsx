import Card from "../../components/common/Card/Card";
import ErrorState from "../../components/common/ErrorState/ErrorState";
import Spinner from "../../components/common/Spinner/Spinner";
import IngredientSearch from "./components/IngredientSearch";
import InventoryList from "./components/InventoryList";
import useInventory from "./hooks/useInventory";

import "./InventoryPanel.css";

/**
 * The signed-in user's saved ingredients: search the catalogue, add,
 * and remove. Render only for signed-in users.
 */
export default function InventoryPanel() {
    const inventory = useInventory();

    let content;

    if (inventory.status === "loading") {
        content = (
            <div className="inventory-panel__center">
                <Spinner label="Loading your ingredients..." />
            </div>
        );
    } else if (inventory.status === "error") {
        content = (
            <ErrorState
                title="Unable to load your ingredients"
                description={inventory.loadError.message}
                onRetry={inventory.reload}
            />
        );
    } else {
        content = (
            <>
                <IngredientSearch
                    ownedIngredientIds={inventory.items.map(
                        (item) => item.ingredient.id
                    )}
                    pendingIds={inventory.pendingAdds}
                    onAdd={inventory.addIngredient}
                />

                <InventoryList
                    items={inventory.items}
                    pendingRemovals={inventory.pendingRemovals}
                    onRemove={inventory.removeItem}
                />
            </>
        );
    }

    return (
        <Card
            title="My ingredients"
            description="Ingredients you have on hand. They're saved to your account."
        >
            <div className="inventory-panel">{content}</div>
        </Card>
    );
}
