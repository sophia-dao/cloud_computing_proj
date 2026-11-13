import { RecipesForYou } from "../../features/recommendations";

import "./HomePage.css";

function HomePage() {
    return (
        <section className="home-page">
            <header className="home-page__intro">
                <h1>Find your next meal</h1>
                <p>
                    Browse recipes, or sign in to save your ingredients and
                    preferences.
                </p>
            </header>

            <RecipesForYou />
        </section>
    );
}

export default HomePage;
