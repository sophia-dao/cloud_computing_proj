import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import ThemeToggle from "../../common/ThemeToggle/ThemeToggle";
import PageContainer from "../PageContainer/PageContainer";

import "./Header.css";

function Header({
    tabs = [],
    logo = null,
    title = "Recipe Suggestion",
})  {
    const [menuOpen, setMenuOpen] = useState(false);

    useEffect(() => {
        if (!menuOpen) return;

        function handleEscape(event) {
            if (event.key === "Escape") {
                setMenuOpen(false);
            }
        }

        window.addEventListener("keydown", handleEscape);
        return () => window.removeEventListener("keydown", handleEscape);
    }, [menuOpen]);

    const renderTabs = (mobile = false) =>
        tabs.map((tab) => (
            <NavLink
                key={tab.path}
                to={tab.path}
                end={tab.path === "/"}
                onClick={mobile ? () => setMenuOpen(false) : undefined}
                className={({ isActive }) =>
                    `site-header__link ${isActive ? "site-header__link--active" : ""
                    }`
                }
            >
                {tab.label}
            </NavLink>
        ));

    return (
        <header className="site-header">
            <PageContainer>
                <div className="site-header__content">
                    <NavLink to="/" className="site-header__brand">
                        {logo && (
                            <span className="site-header__logo">
                                <img src={logo} alt="" />
                            </span>
                        )}

                        <span className="site-header__brand-name">
                            {title}
                        </span>
                    </NavLink>

                    {/* Desktop navigation */}
                    <nav
                        className="site-header__desktop-nav"
                        aria-label="Main navigation"
                    >
                        {renderTabs()}
                        <ThemeToggle />
                    </nav>

                    {/* Mobile hamburger button */}
                    <button
                        type="button"
                        className="site-header__menu-button"
                        aria-label={menuOpen ? "Close menu" : "Open menu"}
                        aria-expanded={menuOpen}
                        aria-controls="mobile-navigation"
                        onClick={() => setMenuOpen((current) => !current)}
                    >
                        {menuOpen ? "✕" : "☰"}
                    </button>
                </div>
            </PageContainer>

            {/* Mobile navigation */}
            <div
                id="mobile-navigation"
                className={`site-header__mobile-panel ${menuOpen ? "site-header__mobile-panel--open" : ""
                    }`}
                inert={!menuOpen}
            >
                <nav aria-label="Mobile navigation">
                    {renderTabs(true)}
                </nav>

                <div className="site-header__mobile-footer">
                    <span>Appearance</span>
                    <ThemeToggle />
                </div>
            </div>

            {menuOpen && (
                <button
                    type="button"
                    className="site-header__backdrop"
                    aria-label="Close navigation menu"
                    onClick={() => setMenuOpen(false)}
                />
            )}
        </header>
    );
}

export default Header;