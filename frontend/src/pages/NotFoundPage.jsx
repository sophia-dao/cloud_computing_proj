import { Link } from "react-router-dom";

function NotFoundPage() {
    return (
        <section>
            <h1>Page Not Found</h1>
            <p>The page you requested does not exist.</p>
            <Link to="/">Return Home</Link>
        </section>
    );
}

export default NotFoundPage;