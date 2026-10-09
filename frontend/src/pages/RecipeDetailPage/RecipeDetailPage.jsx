import { useParams } from "react-router-dom";

export default function RecipeDetailPage() {
    const { id } = useParams();

    return (
        <section>
            <h1>Recipe Details</h1>
            <p>Recipe ID: {id}</p>
            <p>
                Recipe details and ingredient information will be
                implemented in a future issue.
            </p>
        </section>
    );
}