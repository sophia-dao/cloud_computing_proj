
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

/*
 * Authentication hook. The auth feature registers a provider so this client
 * can attach `Authorization: Bearer <access token>` without depending on it.
 *   provider.getToken({ forceRefresh }) -> Promise<string | null>
 */
let authTokenProvider = null;

export function setAuthTokenProvider(provider) {
    authTokenProvider = provider;
}

async function getToken(options) {
    if (!authTokenProvider) return null;

    try {
        return await authTokenProvider.getToken(options);
    } catch {
        return null;
    }
}

async function request(endpoint, options = {}) {
    // `auth: false` skips the bearer token (e.g. for third-party URLs).
    const { headers: customHeaders, auth = true, ...fetchOptions } = options;

    const headers = new Headers(customHeaders);

    // FormData (file uploads) must keep the multipart Content-Type the
    // browser generates, so only plain bodies are labelled as JSON.
    const isFormData =
        typeof FormData !== "undefined" && fetchOptions.body instanceof FormData;

    if (fetchOptions.body != null && !isFormData && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    try {
        const send = async (token) => {
            if (token) headers.set("Authorization", `Bearer ${token}`);
            else headers.delete("Authorization");

            return fetch(`${API_BASE_URL}${endpoint}`, {
                cache: "no-store",
                ...fetchOptions,
                headers,
            });
        };

        const token = auth ? await getToken() : null;
        let response = await send(token);

        // A rejected token: refresh once and retry. If the session can't be
        // refreshed, retry as a guest so public endpoints keep working.
        if (response.status === 401 && token) {
            const refreshed = await getToken({ forceRefresh: true });
            response = await send(refreshed);
        }

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

    /** multipart/form-data upload, e.g. a recipe image. */
    postForm(endpoint, formData, options = {}) {
        return request(endpoint, {
            ...options,
            method: "POST",
            body: formData,
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
