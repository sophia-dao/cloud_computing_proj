import { useCallback, useEffect, useState } from "react";

import allergensApi from "../../../services/AllergensApi";
import tagsApi from "../../../services/TagsApi";
import userService from "../../../services/userService";
import { parseApiError } from "../../../utils/apiErrors";

const toList = (data) =>
    Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

const idsOf = (items) => items.map((item) => item.id);

/**
 * Loads the signed-in user's profile, preferences and allergies together
 * with the reference lists (tags, allergens), and exposes save functions
 * that update local state from the server's response so the UI always
 * shows what was actually persisted.
 */
export default function useProfileSettings() {
    const [status, setStatus] = useState("loading"); // loading | ready | error
    const [loadError, setLoadError] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    const [user, setUser] = useState(null);
    const [tags, setTags] = useState([]);
    const [allergens, setAllergens] = useState([]);
    const [preferenceIds, setPreferenceIds] = useState([]);
    const [allergyIds, setAllergyIds] = useState([]);

    useEffect(() => {
        const controller = new AbortController();
        const options = { signal: controller.signal };

        Promise.all([
            userService.getCurrentUser(options),
            userService.getPreferences(options),
            userService.getAllergies(options),
            tagsApi.getTags(options),
            allergensApi.getAllergens(options),
        ])
            .then(([me, preferences, allergies, allTags, allAllergens]) => {
                if (controller.signal.aborted) return;

                setUser(me);
                setPreferenceIds(idsOf(preferences));
                setAllergyIds(idsOf(allergies));
                setTags(toList(allTags));
                setAllergens(toList(allAllergens));
                setStatus("ready");
            })
            .catch((error) => {
                if (controller.signal.aborted || error?.name === "AbortError") {
                    return;
                }

                setLoadError(parseApiError(error));
                setStatus("error");
            });

        return () => controller.abort();
    }, [reloadKey]);

    const reload = useCallback(() => {
        setStatus("loading");
        setLoadError(null);
        setReloadKey((key) => key + 1);
    }, []);

    const saveProfile = useCallback(async (values) => {
        setUser(await userService.updateCurrentUser(values));
    }, []);

    const savePreferences = useCallback(async (tagIds) => {
        setPreferenceIds(idsOf(await userService.updatePreferences(tagIds)));
    }, []);

    const saveAllergies = useCallback(async (allergenIds) => {
        setAllergyIds(idsOf(await userService.updateAllergies(allergenIds)));
    }, []);

    return {
        status,
        loadError,
        reload,
        user,
        tags,
        allergens,
        preferenceIds,
        allergyIds,
        saveProfile,
        savePreferences,
        saveAllergies,
    };
}
