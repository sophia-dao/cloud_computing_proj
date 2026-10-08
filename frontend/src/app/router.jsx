import { createBrowserRouter } from "react-router-dom";

import Layout from "../components/layout/Layout";
import HomePage from "../pages/HomePage/HomePage";
import NotFoundPage from "../pages/NotFoundPage/NotFoundPage";
import UIDocsPage from "../pages/UIDocsPage/UIDocsPage";

const router = createBrowserRouter([
    {
        path: "/",
        element: <Layout />,
        errorElement: <NotFoundPage />,
        children: [
            {
                index: true,
                element: <HomePage />,
            },
            {
                path: "ui-docs",
                element: <UIDocsPage />,
            },
        ],
    },
]);

export default router;