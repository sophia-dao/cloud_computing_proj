
import Spinner from "../../../components/common/Spinner/Spinner";

function SpinnerExamples() {
    return (
        <div className="ui-docs__example-stack">
            <h4>Available Sizes</h4>

            <div className="ui-docs__example-row">
                <Spinner size="sm" label="Small loading indicator" />
                <Spinner size="md" label="Medium loading indicator" />
                <Spinner size="lg" label="Large loading indicator" />
            </div>
        </div>
    );
}

export default SpinnerExamples;
