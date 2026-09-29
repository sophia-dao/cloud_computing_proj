const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function request(endpoint, options = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

export const apiClient = {
    get(endpoint) {
        return request(endpoint);
    },

    post(endpoint, data) {
        return request(endpoint, {
            method: "POST",
            body: JSON.stringify(data),
        });
    },

    put(endpoint, data) {
        return request(endpoint, {
            method: "PUT",
            body: JSON.stringify(data),
        });
    },

    patch(endpoint, data) {
        return request(endpoint, {
            method: "PATCH",
            body: JSON.stringify(data),
        });
    },

    delete(endpoint) {
        return request(endpoint, {
            method: "DELETE",
        });
    },
};