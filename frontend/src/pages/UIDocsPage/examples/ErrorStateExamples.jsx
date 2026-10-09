
import { useState } from "react";
import ErrorState from "../../../components/common/ErrorState/ErrorState";

function ErrorStateExamples() {
    const [retryCount, setRetryCount] = useState(0);

    return (
        <div className="ui-docs__example-stack">
            <ErrorState
                title="Failed to Load Recipes"
                description="Unable to connect to the recipe service."
                onRetry={() => setRetryCount((count) => count + 1)}
            />

            <p>
                Retry button clicked: <strong>{retryCount}</strong>
            </p>
        </div>
    );
}

export default ErrorStateExamples;
