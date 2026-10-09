
import { createBrowserRouter } from "react-router-dom";

import Layout from "../components/layout/Layout";

import HomePage from "../pages/HomePage/HomePage";
import NotFoundPage from "../pages/NotFoundPage/NotFoundPage";
import UIDocsPage from "../pages/UIDocsPage/UIDocsPage";

import RecipeSearchPage from "../pages/RecipeSearchPage/RecipeSearchPage";
import RecipeDetailPage from "../pages/RecipeDetailPage/RecipeDetailPage";
import DashboardPage from "../pages/DashboardPage/DashboardPage";
import ProfilePage from "../pages/ProfilePage/ProfilePage";
import LoginPage from "../pages/LoginPage/LoginPage";

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
                path: "recipes",
                element: <RecipeSearchPage />,
            },
            {
                path: "recipes/:id",
                element: <RecipeDetailPage />,
            },
            {
                path: "dashboard",
                element: <DashboardPage />,
            },
            {
                path: "profile",
                element: <ProfilePage />,
            },
            {
                path: "login",
                element: <LoginPage />,
            },
            {
                path: "ui-docs",
                element: <UIDocsPage />,
            },
            {
                path: "*",
                element: <NotFoundPage />,
            },
        ],
    },
]);

export default router;
