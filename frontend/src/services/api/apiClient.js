const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        cache: "no-store",
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = new Error(`API request failed: ${response.status}`);
        error.status = response.status;
        throw error;
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

const apiClient = {
    get(endpoint, options = {}) {
        return request(endpoint, {
            ...options,
            method: "GET",
        });
    },

    post(endpoint, data, options = {}) {
        return request(endpoint, {
            ...options,
            method: "POST",
            body: JSON.stringify(data),
        });
    },

    patch(endpoint, data, options = {}) {
        return request(endpoint, {
            ...options,
            method: "PATCH",
            body: JSON.stringify(data),
        });
    },

    delete(endpoint, options = {}) {
        return request(endpoint, {
            ...options,
            method: "DELETE",
        });
    },
};

export default apiClient;