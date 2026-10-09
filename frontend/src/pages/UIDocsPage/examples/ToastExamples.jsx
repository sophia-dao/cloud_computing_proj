
import Button from "../../../components/common/Button/Button";
import { useToast } from "../../../hooks/useToast";

function ToastExamples() {
    const { showToast } = useToast();

    return (
        <div className="ui-docs__example-stack">
            <div className="ui-docs__example-row">
                <Button
                    onClick={() =>
                        showToast({
                            type: "success",
                            message: "Recipe saved successfully!",
                        })
                    }
                >
                    Success
                </Button>

                <Button
                    variant="accent"
                    onClick={() =>
                        showToast({
                            type: "error",
                            message: "Failed to update inventory.",
                        })
                    }
                >
                    Error
                </Button>

                <Button
                    variant="secondary"
                    onClick={() =>
                        showToast({
                            type: "warning",
                            message: "Some ingredients are unavailable.",
                        })
                    }
                >
                    Warning
                </Button>

                <Button
                    variant="ghost"
                    onClick={() =>
                        showToast({
                            type: "info",
                            message: "Preferences updated.",
                        })
                    }
                >
                    Info
                </Button>
            </div>
        </div>
    );
}

export default ToastExamples;
