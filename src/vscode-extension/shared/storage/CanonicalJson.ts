export const toCanonicalJson = (value: unknown): string => {
    if (value === null || typeof value !== 'object') {
        return JSON.stringify(value);
    }

    if (Array.isArray(value)) {
        return `[${value.map(item => toCanonicalJson(item)).join(',')}]`;
    }

    const entries = Object.keys(value as Record<string, unknown>)
        .sort()
        .map(key => `${JSON.stringify(key)}:${toCanonicalJson((value as Record<string, unknown>)[key])}`);

    return `{${entries.join(',')}}`;
};

