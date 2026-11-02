
/**
 * Convert recipe tags into Select-compatible options.
 *
 * @param {Array} tags - Tags returned by the API.
 * @param {string} type - Tag type (CUISINE, DIET, COST, OTHER).
 * @param {string} defaultLabel - Label for the empty selection.
 * @returns {Array<{label: string, value: string}>}
 */
export function buildTagOptions(tags, type, defaultLabel) {
    return [
        { label: defaultLabel, value: "" },
        ...tags
            .filter((tag) => tag.type === type)
            .map((tag) => ({
                label: tag.name,
                value: tag.name,
            })),
    ];
}
