import apiClient from "./api/apiClient";

const tagsApi = {
    getTags({ signal } = {}) {
        return apiClient.get("/tags/", { signal });
    },
};

export default tagsApi;