import Badge from "../../../components/common/Badge/Badge";
import EmptyState from "../../../components/common/EmptyState/EmptyState";

export default function InventoryList({ items, pendingRemovals, onRemove }) {
    if (items.length === 0) {
        return (
            <EmptyState
                icon="🥕"
                title="No ingredients saved yet"
                description="Search above and add what you have in your kitchen."
            />
        );
    }

    return (
        <ul className="inventory-list" aria-label="Your saved ingredients">
            {items.map((item) => (
                <li key={item.id}>
                    <Badge
                        variant="accent"
                        removable
                        disabled={pendingRemovals.includes(item.id)}
                        onRemove={() => onRemove(item)}
                    >
                        {item.ingredient.name}
                    </Badge>
                </li>
            ))}
        </ul>
    );
}
