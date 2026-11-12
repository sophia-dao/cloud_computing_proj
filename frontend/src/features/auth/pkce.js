/** PKCE (RFC 7636) and state helpers using the Web Crypto API. */

function base64UrlEncode(bytes) {
    let binary = "";
    bytes.forEach((byte) => {
        binary += String.fromCharCode(byte);
    });
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Cryptographically random, URL-safe string (43+ chars for a verifier). */
export function randomString(byteLength = 32) {
    const bytes = new Uint8Array(byteLength);
    crypto.getRandomValues(bytes);
    return base64UrlEncode(bytes);
}

export async function createCodeChallenge(verifier) {
    const digest = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(verifier)
    );
    return base64UrlEncode(new Uint8Array(digest));
}

/** Decodes a JWT payload for display/expiry only. The backend verifies signatures. */
export function decodeJwtPayload(token) {
    try {
        const payload = String(token).split(".")[1];
        if (!payload) return null;
        const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
        const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
        const json = decodeURIComponent(
            Array.from(atob(padded), (char) =>
                `%${char.charCodeAt(0).toString(16).padStart(2, "0")}`
            ).join("")
        );
        return JSON.parse(json);
    } catch {
        return null;
    }
}
