
const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"
).replace(/\/+$/, "");

export class ApiError extends Error {
    constructor(message, status = null, data = null) {
        super(message);

        this.name = "ApiError";
        this.status = status;
        this.data = data;
    }
}

async function request(endpoint, options = {}) {
    const { headers: customHeaders, ...fetchOptions } = options;

    const headers = new Headers(customHeaders);

    if (fetchOptions.body != null && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            cache: "no-store",
            ...fetchOptions,
            headers,
        });

        const contentType = response.headers.get("content-type") || "";

        let data = null;

        if (response.status !== 204 && response.status !== 205) {
            if (contentType.includes("application/json")) {
                data = await response.json();
            } else {
                const text = await response.text();
                data = text || null;
            }
        }

        if (!response.ok) {
            const message =
                (typeof data?.detail === "string" && data.detail) ||
                (typeof data?.message === "string" && data.message) ||
                `API request failed: ${response.status}`;

            throw new ApiError(message, response.status, data);
        }

        return data;
    } catch (error) {
        if (error instanceof ApiError) {
            throw error;
        }

        // Preserve cancellation so callers can ignore aborted requests.
        if (error.name === "AbortError") {
            throw error;
        }

        if (error instanceof TypeError) {
            throw new ApiError(
                "Unable to connect to the server. Please check your connection."
            );
        }

        throw error;
    }
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

    put(endpoint, data, options = {}) {
        return request(endpoint, {
            ...options,
            method: "PUT",
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
