import { Link, Outlet } from "react-router-dom";

function Layout() {
    return (
        <>
            <header>
                <nav>
                    <Link to="/">Recipe Suggestion</Link>
                </nav>
            </header>

            <main>
                <Outlet />
            </main>
        </>
    );
}

export default Layout;