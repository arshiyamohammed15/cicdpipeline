/**
 * Storage Path Resolver (VS Code Extension)
 * 
 * Resolves storage paths according to 4-Plane Storage Architecture rules.
 * Ensures compliance with Rule 223: Path resolution via ZU_ROOT environment variable.
 * 
 * @module storage
 */

import * as vscode from 'vscode';

/**
 * Storage plane types
 */
export type StoragePlane = 'ide' | 'tenant' | 'product' | 'shared';

/**
 * Storage path resolver for VS Code Extension
 * All paths must be resolved via ZU_ROOT environment variable (Rule 223).
 */
export class StoragePathResolver {
    private zuRoot: string;

    constructor(zuRoot?: string) {
        // Get ZU_ROOT from environment variable or VS Code configuration
        this.zuRoot = zuRoot || 
                     process.env.ZU_ROOT || 
                     vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') || 
                     '';

        if (!this.zuRoot) {
            throw new Error('ZU_ROOT environment variable or zeroui.zuRoot configuration is required for storage operations');
        }

        // Normalize path
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
     * @param relativePath Relative path within IDE plane
     */
    public resolveIdePath(relativePath: string): string {
        return this.resolvePlanePath('ide', relativePath);
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

        // Validate year
        if (year < 2000 || year > 9999) {
            throw new Error(`Invalid year: ${year}. Must be 4 digits (YYYY)`);
        }

        // Validate month
        if (month < 1 || month > 12) {
            throw new Error(`Invalid month: ${month}. Must be 1-12`);
        }

        // Format: receipts/{repo-id}/{yyyy}/{mm}/
        const monthStr = month.toString().padStart(2, '0');
        const relativePath = `receipts/${repoId}/${year}/${monthStr}/`;
        
        return this.resolveIdePath(relativePath);
    }

    /**
     * Resolve path for a specific storage plane
     */
    private resolvePlanePath(plane: StoragePlane, relativePath: string): string {
        // Validate plane name (kebab-case only per Rule 216)
        if (!this.isKebabCase(plane)) {
            throw new Error(`Invalid plane name: ${plane}. Must be kebab-case [a-z0-9-] only`);
        }

        // Validate relative path components
        const pathParts = relativePath.split('/').filter(p => p.length > 0);
        for (const part of pathParts) {
            if (!this.isKebabCase(part)) {
                throw new Error(`Invalid path component: ${part}. Must be kebab-case [a-z0-9-] only`);
            }
        }

        // Construct full path
        const normalizedRelative = relativePath.replace(/^\/+|\/+$/g, '');
        const fullPath = `${this.zuRoot}/${plane}/${normalizedRelative}`;
        
        return this.normalizePath(fullPath);
    }

    /**
     * Validate kebab-case naming (Rule 216)
     */
    private isKebabCase(value: string): boolean {
        const kebabCasePattern = /^[a-z0-9-]+$/;
        return kebabCasePattern.test(value);
    }

    /**
     * Normalize path separators
     */
    private normalizePath(pathStr: string): string {
        return pathStr.replace(/\\/g, '/').replace(/\/+/g, '/');
    }
}

