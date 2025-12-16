/**
 * Base Storage Path Resolver
 *
 * Provides shared 4-Plane storage resolution logic for all runtimes.
 * Ensures consistent enforcement of ZU_ROOT requirements and kebab-case rules.
 */

export type StoragePlane = 'ide' | 'tenant' | 'product' | 'shared';

export class BaseStoragePathResolver {
    protected zuRoot: string;

    constructor(zuRoot: string) {
        if (!zuRoot) {
            throw new Error('ZU_ROOT environment variable is required for storage operations');
        }

        this.zuRoot = this.normalizePath(zuRoot);
    }

    /**
     * Get the normalized ZU_ROOT path.
     */
    public getZuRoot(): string {
        return this.zuRoot;
    }

    /**
     * Resolve path for IDE plane.
     */
    public resolveIdePath(relativePath: string): string {
        return this.resolvePlanePath('ide', relativePath);
    }

    /**
     * Resolve path for Tenant plane.
     */
    public resolveTenantPath(relativePath: string): string {
        return this.resolvePlanePath('tenant', relativePath);
    }

    /**
     * Resolve path for Product plane.
     */
    public resolveProductPath(relativePath: string): string {
        return this.resolvePlanePath('product', relativePath);
    }

    /**
     * Resolve path for Shared plane.
     */
    public resolveSharedPath(relativePath: string): string {
        return this.resolvePlanePath('shared', relativePath);
    }

    /**
     * Resolve receipt storage path (IDE plane).
     */
    public resolveReceiptPath(repoId: string, year: number, month: number): string {
        this.assertKebabCase(repoId, 'repo-id');

        if (year < 2000 || year > 9999) {
            throw new Error(`Invalid year: ${year}. Must be 4 digits (YYYY)`);
        }

        if (month < 1 || month > 12) {
            throw new Error(`Invalid month: ${month}. Must be 1-12`);
        }

        const monthStr = month.toString().padStart(2, '0');
        const relativePath = `receipts/${repoId}/${year}/${monthStr}/`;
        return this.resolveIdePath(relativePath);
    }

    /**
     * Resolve policy storage path.
     */
    public resolvePolicyPath(plane: 'ide' | 'product', subPath: string = ''): string {
        if (plane === 'ide') {
            const relativePath = subPath ? `policy/${subPath}` : 'policy/';
            return this.resolveIdePath(relativePath);
        }

        const relativePath = subPath ? `policy/registry/${subPath}` : 'policy/registry/';
        return this.resolvePlanePath('product', relativePath);
    }

    /**
     * Resolve path for any storage plane with validation.
     */
    public resolvePlanePath(plane: StoragePlane, relativePath: string): string {
        // CR-001: Validate input
        if (!relativePath || typeof relativePath !== 'string') {
            throw new Error('relativePath cannot be empty or null');
        }

        // CR-004: Runtime type validation for StoragePlane
        const validPlanes: StoragePlane[] = ['ide', 'tenant', 'product', 'shared'];
        if (!validPlanes.includes(plane)) {
            throw new Error(`Invalid storage plane: ${plane}. Must be one of: ${validPlanes.join(', ')}`);
        }

        this.assertKebabCase(plane, 'plane name');

        const pathParts = relativePath.split('/').filter(part => part.length > 0);
        for (const part of pathParts) {
            // CR-002: Path traversal vulnerability check
            if (part === '..' || part === '.' || part.startsWith('/') || part.includes('\\')) {
                throw new Error(`Invalid path component: ${part}. Path traversal not allowed`);
            }
            this.assertKebabCase(part, 'path component');
        }

        const normalizedRelative = relativePath.replace(/^\/+|\/+$/g, '');
        const fullPath = `${this.zuRoot}/${plane}/${normalizedRelative}`;
        return this.normalizePath(fullPath);
    }

    protected isKebabCase(value: string): boolean {
        const kebabCasePattern = /^[a-z0-9-]+$/;
        return kebabCasePattern.test(value);
    }

    protected assertKebabCase(value: string, label: string): void {
        if (!this.isKebabCase(value)) {
            throw new Error(`Invalid ${label}: ${value}. Must be kebab-case [a-z0-9-] only`);
        }
    }

    protected normalizePath(pathStr: string): string {
        if (!pathStr || typeof pathStr !== 'string') {
            throw new Error('pathStr must be a non-empty string');
        }

        // CR-003: Handle edge cases - Windows UNC paths and multiple slashes
        // Preserve UNC path prefix (\\server\share) if present
        let normalized = pathStr.replace(/\\/g, '/');
        
        // Handle UNC paths: \\server\share -> //server/share
        if (normalized.startsWith('//')) {
            // Keep UNC prefix, normalize rest
            const uncMatch = normalized.match(/^(\/\/[^\/]+)(\/.*)?$/);
            if (uncMatch) {
                const uncPrefix = uncMatch[1];
                const rest = uncMatch[2] || '';
                normalized = uncPrefix + rest.replace(/\/+/g, '/');
                return normalized;
            }
        }
        
        // Normalize multiple slashes, but preserve leading slash for absolute paths
        const isAbsolute = normalized.startsWith('/');
        normalized = normalized.replace(/\/+/g, '/');
        
        // Remove trailing slashes except for root
        if (normalized.length > 1 && normalized.endsWith('/')) {
            normalized = normalized.slice(0, -1);
        }
        
        return normalized;
    }
}

