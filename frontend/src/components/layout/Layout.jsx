import { Outlet } from "react-router-dom";

import { navigationTabs } from "../../app/navigation";

import Header from "./Header/Header";
import PageContainer from "./PageContainer/PageContainer";

function Layout() {
    return (
        <>
            <Header tabs={navigationTabs} />

            <main>
                <PageContainer>
                    <Outlet />
                </PageContainer>
            </main>
        </>
    );
}

export default Layout;