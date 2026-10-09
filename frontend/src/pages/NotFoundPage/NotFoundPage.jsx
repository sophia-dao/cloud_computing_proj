import { Link } from "react-router-dom";
import "./NotFoundPage.css";

export default function NotFoundPage() {
    return (
        <main className="not-found">
            <div className="not-found__content">
                <div className="not-found__illustration" aria-hidden="true">
                    <span className="not-found__leaf">🥬</span>
                    <div className="not-found__illustration" aria-hidden="true">
                        <span className="not-found__leaf">🥬</span>

                        <img
                            src="/thief.webp"
                            alt=""
                            className="not-found__thief"
                        />
                    </div>
                </div>

                <h1 className="not-found__code">404</h1>

                <h2 className="not-found__title">
                    This page is taking an absent leave.
                </h2>

                <p className="not-found__description">
                    And so is our developer&apos;s grade 100 security.
                </p>

                <Link to="/" className="not-found__button">
                    Blame Sophia 👀 <span aria-hidden="true">→</span>
                </Link>
                <p className="not-found__footer">
                    She drafted the blue print.
                </p>
            </div>
        </main>
    );
}