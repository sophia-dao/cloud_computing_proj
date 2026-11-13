import { useEffect, useRef, useState } from "react";

import Button from "../../components/common/Button/Button";
import Select from "../../components/common/Select/Select";
import IngredientPicker from "../../features/ingredients/components/IngredientPicker";
import useIngredientSelection from "../../features/ingredients/hooks/useIngredientSelection";
import RecommendationResults from "../../features/recommendations/components/RecommendationResults";
import recommendationService, {
    MATCH_MODES,
} from "../../services/api/recommendationService";

import "./IngredientRecommendationPage.css";

const MATCH_MODE_OPTIONS = [
    { value: MATCH_MODES.PARTIAL_MATCH, label: "Partial match — use some of my ingredients" },
    { value: MATCH_MODES.AVAILABLE_ONLY, label: "Only what I have — no missing ingredients" },
];

function toResults(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.results)) return data.results;
    return [];
}

function describeError(error) {
    const status = error?.status;
    if (status === 404 || status >= 500) {
        return "The recommendation service isn't available right now. Please try again later.";
    }
    if (status === 429) return "Too many requests. Please wait a moment and try again.";
    // Validation (400) and connection errors carry a readable message.
    return error?.message || "Unable to load recommendations.";
}

export default function IngredientRecommendationPage() {
    const { selected, selectedIds, add, remove, clear } = useIngredientSelection();
    const [matchMode, setMatchMode] = useState(MATCH_MODES.PARTIAL_MATCH);

    const [request, setRequest] = useState({
        status: "idle",
        results: [],
        error: "",
    });

    const controllerRef = useRef(null);

    // Cancel any pending request when leaving the page.
    useEffect(() => () => controllerRef.current?.abort(), []);

    async function submit() {
        if (!selectedIds.length) return;

        controllerRef.current?.abort();
        const controller = new AbortController();
        controllerRef.current = controller;

        setRequest({ status: "loading", results: [], error: "" });

        try {
            const data = await recommendationService.getRecommendations(
                { ingredientIds: selectedIds, matchMode },
                { signal: controller.signal }
            );

            if (!controller.signal.aborted) {
                setRequest({ status: "success", results: toResults(data), error: "" });
            }
        } catch (error) {
            if (error?.name === "AbortError" || controller.signal.aborted) return;

            setRequest({
                status: "error",
                results: [],
                error: describeError(error),
            });
        }
    }

    function handleSubmit(event) {
        event.preventDefault();
        submit();
    }

    return (
        <div className="ingredient-recommendation-page">
            <header className="ingredient-recommendation-page__header">
                <span className="ingredient-recommendation-page__eyebrow">
                    Cook with what you have
                </span>
                <h1>What&apos;s in your kitchen?</h1>
                <p>
                    Add the ingredients you have on hand and we&apos;ll suggest
                    recipes you can make. Your picks are only kept on this page.
                </p>
            </header>

            <form
                className="ingredient-recommendation-page__panel"
                onSubmit={handleSubmit}
                noValidate
            >
                <IngredientPicker
                    selected={selected}
                    onAdd={add}
                    onRemove={remove}
                    onClear={clear}
                    disabled={request.status === "loading"}
                />

                <div className="ingredient-recommendation-page__actions">
                    <Select
                        label="Match mode"
                        options={MATCH_MODE_OPTIONS}
                        value={matchMode}
                        onChange={(event) => setMatchMode(event.target.value)}
                        disabled={request.status === "loading"}
                    />

                    <Button
                        type="submit"
                        size="lg"
                        disabled={!selectedIds.length}
                        loading={request.status === "loading"}
                    >
                        Find recipes
                        {selectedIds.length ? ` (${selectedIds.length})` : ""}
                    </Button>
                </div>
            </form>

            <RecommendationResults
                status={request.status}
                results={request.results}
                error={request.error}
                onRetry={submit}
            />
        </div>
    );
}
