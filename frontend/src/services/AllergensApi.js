import apiClient from "./api/apiClient";

const allergensApi = {
    getAllergens({ signal } = {}) {
        return apiClient.get("/users/allergens/", { signal });
    },
};

export default allergensApi;