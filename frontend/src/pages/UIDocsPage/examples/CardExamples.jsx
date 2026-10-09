
import Card from "../../../components/common/Card/Card";
import Button from "../../../components/common/Button/Button";

function CardExamples() {
    return (
        <div className="ui-docs__example-stack">
            <Card
                title="Recipe Card"
                description="A simple card with a title and description."
                bordered
                footer={
                    <Button size="sm">
                        View Recipe
                    </Button>
                }
            >
                <p>
                    Ingredients: Chicken, rice, garlic.
                </p>
                <p>Cooking time: 30 minutes.</p>
            </Card>

            <Card
                title="Floating Card"
                description="A card with a shadow but no border."
                bordered={false}
                floating
            >
                <p>
                    Useful for dashboard widgets and featured content.
                </p>
            </Card>

            <Card
                title="Simple Container"
                bordered={false}
                floating={false}
            >
                <p>
                    A minimal card without a border or shadow.
                </p>
            </Card>
        </div>
    );
}

export default CardExamples;
