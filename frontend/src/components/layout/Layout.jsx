import { Outlet } from "react-router-dom";

import { getVisibleTabs, navigationTabs } from "../../app/navigation";
import AccountControls from "../../features/auth/AccountControls";
import { useAuth } from "../../hooks/useAuth";

import Header from "./Header/Header";
import PageContainer from "./PageContainer/PageContainer";

function Layout() {
    const { isAuthenticated } = useAuth();

    return (
        <>
            <Header
                tabs={getVisibleTabs(navigationTabs, isAuthenticated)}
                actions={<AccountControls />}
            />

            <main>
                <PageContainer>
                    <Outlet />
                </PageContainer>
            </main>
        </>
    );
}

export default Layout;
