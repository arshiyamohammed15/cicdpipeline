/**
 * Storage Path Resolver (VS Code Extension)
 *
 * Resolves storage paths according to 4-Plane Storage Architecture rules.
 * Ensures compliance with Rule 223: Path resolution via ZU_ROOT environment variable.
 *
 * @module storage
 */

import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { BaseStoragePathResolver, StoragePlane } from './BaseStoragePathResolver';

export type { StoragePlane };

/**
 * Storage path resolver for VS Code Extension
 * All paths must be resolved via ZU_ROOT environment variable (Rule 223).
 */
export class StoragePathResolver extends BaseStoragePathResolver {
    constructor(zuRoot?: string) {
        const resolvedZuRoot = zuRoot ||
            process.env.ZU_ROOT ||
            vscode.workspace.getConfiguration('zeroui').get<string>('zuRoot') ||
            '';

        if (!resolvedZuRoot) {
            throw new Error('ZU_ROOT environment variable or zeroui.zuRoot configuration is required for storage operations');
        }

        super(resolvedZuRoot);
    }

    /**
     * Resolve the PSCL temporary directory under the IDE plane.
     * Creates the directory if it does not exist. Falls back to
     * a workspace-local .zeroui/pscl/{repoId} directory if the IDE
     * plane location cannot be created.
     */
    public getPsclTempDir(
        repoId: string,
        options?: { workspaceRoot?: string }
    ): string {
        const normalizedRepoId = repoId.trim();
        this.assertKebabCase(normalizedRepoId, 'repo-id');

        const psclIdePath = this.resolveIdePath(`pscl/${normalizedRepoId}/`);
        try {
            this.ensureDirectory(psclIdePath);
            return psclIdePath;
        } catch (error) {
            const workspaceRoot = options?.workspaceRoot
                ? path.resolve(options.workspaceRoot)
                : path.resolve('.');
            const fallbackDir = path.resolve(
                workspaceRoot,
                '.zeroui',
                'pscl',
                normalizedRepoId
            );
            this.ensureDirectory(fallbackDir);
            return this.normalizePath(fallbackDir);
        }
    }

    private ensureDirectory(dirPath: string): void {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}
