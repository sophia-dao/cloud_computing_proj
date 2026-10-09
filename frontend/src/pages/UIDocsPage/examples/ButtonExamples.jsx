
import Button from "../../../components/common/Button/Button";

function ButtonExamples() {
    return (
        <div className="ui-docs__example-stack">
            <div className="ui-docs__example-row">
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="accent">Accent</Button>
                <Button variant="ghost">Ghost</Button>
            </div>

            <div className="ui-docs__example-row">
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
            </div>

            <div className="ui-docs__example-row">
                <Button disabled>Disabled</Button>
                <Button loading>Loading</Button>
            </div>
        </div>
    );
}

export default ButtonExamples;
