
import Button from "../../../components/common/Button/Button";
import EmptyState from "../../../components/common/EmptyState/EmptyState";

function EmptyStateExamples() {
    return (
        <div className="ui-docs__example-stack">
            <EmptyState
                icon="🍳"
                title="No Matching Recipes"
                description="Try adding more ingredients or adjusting your filters."
                action={
                    <Button
                        variant="secondary"
                        onClick={() => window.alert("Demo: Clear filters")}
                    >
                        Clear Filters
                    </Button>
                }
            />

            <EmptyState
                icon="📦"
                title="Your Inventory Is Empty"
                description="Add ingredients to start getting recipe suggestions."
            />
        </div>
    );
}

export default EmptyStateExamples;
