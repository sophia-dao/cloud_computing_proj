import { Link, Outlet } from "react-router-dom";
import ThemeToggle from "../common/ThemeToggle/ThemeToggle";

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
            <ThemeToggle />
        </>
    );
}

export default Layout;