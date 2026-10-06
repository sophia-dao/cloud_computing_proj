import { useEffect, useState } from "react";

import { getHealth } from "../services/healthService";

function HomePage() {
    const [backendStatus, setBackendStatus] = useState("Checking...");

    useEffect(() => {
        async function checkBackend() {
            try {
                const data = await getHealth();
                setBackendStatus(data.status ?? "Connected");
            } catch {
                setBackendStatus("Unavailable");
            }
        }

        checkBackend();
    }, []);

    return (
        <section>
            <h1>Recipe Suggestion</h1>
            <p>Find recipes using ingredients you already have.</p>

            <p>
                Backend status: <strong>{backendStatus}</strong>
            </p>
        </section>
    );
}

export default HomePage;