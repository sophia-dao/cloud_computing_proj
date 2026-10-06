import apiClient from "./api/apiClient";

export function getHealth() {
    return apiClient.get("/health/");
}