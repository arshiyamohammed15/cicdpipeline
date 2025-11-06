/**
 * Storage Path Resolver
 * 
 * Resolves storage paths according to 4-Plane Storage Architecture rules.
 * Ensures compliance with Rule 223: Path resolution via ZU_ROOT environment variable.
 * 
 * @module storage
 */

/**
 * Storage plane types
 */
export type StoragePlane = 'ide' | 'tenant' | 'product' | 'shared';

/**
 * Storage path resolver that ensures compliance with storage governance rules.
 * All paths must be resolved via ZU_ROOT environment variable (Rule 223).
 */
export class StoragePathResolver {
    private zuRoot: string;

    constructor(zuRoot?: string) {
        // Get ZU_ROOT from environment variable if not provided
        this.zuRoot = zuRoot || process.env.ZU_ROOT || '';
        
        if (!this.zuRoot) {
            throw new Error('ZU_ROOT environment variable is required for storage operations');
        }

        // Normalize path (handle Windows/Unix separators)
        this.zuRoot = this.normalizePath(this.zuRoot);
    }

    /**
     * Get the base ZU_ROOT path
     */
    public getZuRoot(): string {
        return this.zuRoot;
    }

    /**
     * Resolve path for IDE plane
     * @param relativePath Relative path within IDE plane (e.g., 'receipts/repo-id/2025/10/')
     */
    public resolveIdePath(relativePath: string): string {
        return this.resolvePlanePath('ide', relativePath);
    }

    /**
     * Resolve path for Tenant plane
     * @param relativePath Relative path within Tenant plane
     */
    public resolveTenantPath(relativePath: string): string {
        return this.resolvePlanePath('tenant', relativePath);
    }

    /**
     * Resolve path for Product plane
     * @param relativePath Relative path within Product plane
     */
    public resolveProductPath(relativePath: string): string {
        return this.resolvePlanePath('product', relativePath);
    }

    /**
     * Resolve path for Shared plane
     * @param relativePath Relative path within Shared plane
     */
    public resolveSharedPath(relativePath: string): string {
        return this.resolvePlanePath('shared', relativePath);
    }

    /**
     * Resolve path for a specific storage plane
     * @param plane Storage plane (ide, tenant, product, shared)
     * @param relativePath Relative path within the plane
     */
    private resolvePlanePath(plane: StoragePlane, relativePath: string): string {
        // Validate plane name (kebab-case only per Rule 216)
        if (!this.isKebabCase(plane)) {
            throw new Error(`Invalid plane name: ${plane}. Must be kebab-case [a-z0-9-] only`);
        }

        // Validate relative path (kebab-case only per Rule 216)
        const pathParts = relativePath.split('/').filter(p => p.length > 0);
        for (const part of pathParts) {
            if (!this.isKebabCase(part)) {
                throw new Error(`Invalid path component: ${part}. Must be kebab-case [a-z0-9-] only`);
            }
        }

        // Construct full path: {ZU_ROOT}/{plane}/{relativePath}
        const normalizedRelative = relativePath.replace(/^\/+|\/+$/g, ''); // Remove leading/trailing slashes
        const fullPath = `${this.zuRoot}/${plane}/${normalizedRelative}`;
        
        return this.normalizePath(fullPath);
    }

    /**
     * Resolve receipt storage path (IDE Plane)
     * Pattern: ide/receipts/{repo-id}/{yyyy}/{mm}/ (Rule 228: YYYY/MM month partitioning)
     * 
     * @param repoId Repository identifier (kebab-case)
     * @param year 4-digit year (YYYY)
     * @param month 2-digit month (MM)
     */
    public resolveReceiptPath(repoId: string, year: number, month: number): string {
        // Validate kebab-case repo-id (Rule 216)
        if (!this.isKebabCase(repoId)) {
            throw new Error(`Invalid repo-id: ${repoId}. Must be kebab-case [a-z0-9-] only`);
        }

        // Validate year (must be 4 digits)
        if (year < 2000 || year > 9999) {
            throw new Error(`Invalid year: ${year}. Must be 4 digits (YYYY)`);
        }

        // Validate month (must be 1-12)
        if (month < 1 || month > 12) {
            throw new Error(`Invalid month: ${month}. Must be 1-12`);
        }

        // Format: receipts/{repo-id}/{yyyy}/{mm}/
        const monthStr = month.toString().padStart(2, '0');
        const relativePath = `receipts/${repoId}/${year}/${monthStr}/`;
        
        return this.resolveIdePath(relativePath);
    }

    /**
     * Resolve policy storage path (IDE Plane for cache, Product Plane for registry)
     * Pattern: ide/policy/ or product/policy/registry/
     * 
     * @param plane Storage plane (ide for cache, product for registry)
     * @param subPath Sub-path within policy directory
     */
    public resolvePolicyPath(plane: 'ide' | 'product', subPath: string = ''): string {
        if (plane === 'ide') {
            const relativePath = subPath ? `policy/${subPath}` : 'policy/';
            return this.resolveIdePath(relativePath);
        } else {
            const relativePath = subPath ? `policy/registry/${subPath}` : 'policy/registry/';
            return this.resolveProductPath(relativePath);
        }
    }

    /**
     * Validate kebab-case naming (Rule 216)
     * Pattern: [a-z0-9-] only
     */
    private isKebabCase(value: string): boolean {
        const kebabCasePattern = /^[a-z0-9-]+$/;
        return kebabCasePattern.test(value);
    }

    /**
     * Normalize path separators (handle Windows/Unix)
     */
    private normalizePath(path: string): string {
        // Replace backslashes with forward slashes
        return path.replace(/\\/g, '/').replace(/\/+/g, '/');
    }
}

