import { createBrowserRouter } from "react-router-dom";

import Layout from "../components/layout/Layout";
import HomePage from "../pages/HomePage";
import NotFoundPage from "../pages/NotFoundPage";

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
        ],
    },
]);

export default router;