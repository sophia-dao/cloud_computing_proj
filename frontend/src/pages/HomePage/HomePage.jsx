
import { useState } from "react";

import Button from "../../components/common/Button/Button";
import FormCard from "../../components/common/FormCard/FormCard";
import Input from "../../components/common/Input/Input";
import Select from "../../components/common/Select/Select";

import "./HomePage.css";

function HomePage() {
    const [form, setForm] = useState({
        ingredient: "",
        cuisine: "",
        difficulty: "",
        maxTime: "",
    });

    const [submitted, setSubmitted] = useState(null);

    function updateField(event) {
        const { name, value } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]: value,
        }));
    }

    function handleSubmit(event) {
        event.preventDefault();
        setSubmitted({ ...form });
    }

    function handleReset() {
        setForm({
            ingredient: "",
            cuisine: "",
            difficulty: "",
            maxTime: "",
        });
        setSubmitted(null);
    }

    return (
        <div className="home-page">
            <section className="home-page__intro">
                <h1>Find Your Next Recipe</h1>
                <p>
                    Discover recipes based on ingredients you already have.
                </p>
            </section>

            <FormCard
                title="Recipe Search"
                description="Enter your ingredients and preferences."
                columns={2}
                bordered={true}
                floating={true}
                onSubmit={handleSubmit}
                footer={
                    <>
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={handleReset}
                        >
                            Reset
                        </Button>

                        <Button type="submit">
                            Find Recipes
                        </Button>
                    </>
                }
            >
                <Input
                    label="Ingredient"
                    name="ingredient"
                    placeholder="e.g. Chicken"
                    value={form.ingredient}
                    onChange={updateField}
                    required
                />

                <Select
                    label="Cuisine"
                    name="cuisine"
                    placeholder="Any cuisine"
                    value={form.cuisine}
                    onChange={updateField}
                    options={[
                        { label: "Vietnamese", value: "vietnamese" },
                        { label: "Italian", value: "italian" },
                        { label: "Japanese", value: "japanese" },
                        { label: "American", value: "american" },
                    ]}
                />

                <Select
                    label="Difficulty"
                    name="difficulty"
                    placeholder="Any difficulty"
                    value={form.difficulty}
                    onChange={updateField}
                    options={[
                        { label: "Easy", value: "easy" },
                        { label: "Medium", value: "medium" },
                        { label: "Hard", value: "hard" },
                    ]}
                />

                <Input
                    label="Maximum Cooking Time"
                    name="maxTime"
                    type="number"
                    placeholder="Minutes"
                    min="1"
                    value={form.maxTime}
                    onChange={updateField}
                />
            </FormCard>

            {submitted && (
                <section className="home-page__result">
                    <h2>Submitted Values</h2>
                    <pre>{JSON.stringify(submitted, null, 2)}</pre>
                    <p>
                        This is a frontend demonstration. Recipe API
                        integration will be added later.
                    </p>
                </section>
            )}
        </div>
    );
}

export default HomePage;
