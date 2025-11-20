"use strict";
/**
 * LocalBackup
 *
 * Local file-based implementation of BackupPort.
 * Uses incremental snapshot manifest + checksums with verify routine.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LocalBackup = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const crypto = __importStar(require("crypto"));
class LocalBackup {
    constructor(baseDir) {
        this.backups = new Map();
        this.baseDir = baseDir;
        this.manifestFile = path.join(baseDir, 'backup-manifest.jsonl');
        this.loadManifests();
    }
    async createBackup(request) {
        const backupId = this.generateBackupId();
        const now = new Date();
        const backupDir = path.join(this.baseDir, 'backups', backupId);
        await this.ensureDirectory(backupDir);
        const manifest = {
            id: backupId,
            resourceId: request.resourceId,
            resourceType: request.resourceType,
            name: request.name,
            description: request.description,
            status: 'creating',
            encrypted: request.encrypted || false,
            createdAt: now.toISOString(),
            files: [],
            checksum: '',
        };
        try {
            // Simulate backup creation (in real implementation, copy files)
            const files = await this.scanResource(request.resourceId, request.resourceType);
            let totalSize = 0;
            for (const file of files) {
                const filePath = path.join(backupDir, file.path);
                await this.ensureDirectory(path.dirname(filePath));
                // Read source file and calculate checksum
                const sourcePath = this.resolveResourcePath(request.resourceId, request.resourceType, file.path);
                if (fs.existsSync(sourcePath)) {
                    const data = await fs.promises.readFile(sourcePath);
                    const checksum = this.calculateChecksum(data);
                    totalSize += data.length;
                    // Write to backup
                    await fs.promises.writeFile(filePath, data);
                    manifest.files.push({
                        path: file.path,
                        checksum,
                        size: data.length,
                        incremental: false,
                    });
                }
            }
            manifest.sizeBytes = totalSize;
            manifest.status = 'completed';
            manifest.completedAt = new Date().toISOString();
            // Calculate checksum after all fields are set
            manifest.checksum = this.calculateManifestChecksum(manifest);
            // Save manifest
            await this.appendToJsonl(this.manifestFile, JSON.stringify(manifest));
            this.backups.set(backupId, manifest);
            return {
                id: backupId,
                resourceId: request.resourceId,
                resourceType: request.resourceType,
                name: request.name,
                description: request.description,
                status: 'completed',
                sizeBytes: totalSize,
                createdAt: now,
                completedAt: new Date(),
                encrypted: manifest.encrypted,
                metadata: manifest.metadata,
            };
        }
        catch (error) {
            manifest.status = 'failed';
            await this.appendToJsonl(this.manifestFile, JSON.stringify(manifest));
            throw error;
        }
    }
    async restoreBackup(backupId, options) {
        const manifest = this.backups.get(backupId);
        if (!manifest) {
            throw new Error(`Backup ${backupId} not found`);
        }
        const targetResourceId = options?.targetResourceId || manifest.resourceId;
        const backupDir = path.join(this.baseDir, 'backups', backupId);
        const startTime = new Date();
        let componentsRestored = 0;
        try {
            for (const file of manifest.files) {
                if (options?.components && !options.components.includes(file.path)) {
                    continue;
                }
                const sourcePath = path.join(backupDir, file.path);
                if (!fs.existsSync(sourcePath)) {
                    throw new Error(`Backup file not found: ${file.path}`);
                }
                const targetPath = this.resolveResourcePath(targetResourceId, manifest.resourceType, file.path);
                await this.ensureDirectory(path.dirname(targetPath));
                // Check if target exists and overwrite is not allowed
                if (fs.existsSync(targetPath) && !options?.overwrite) {
                    throw new Error(`Target file exists and overwrite not allowed: ${targetPath}`);
                }
                const data = await fs.promises.readFile(sourcePath);
                const checksum = this.calculateChecksum(data);
                // Verify checksum
                if (checksum !== file.checksum) {
                    throw new Error(`Checksum mismatch for file: ${file.path}`);
                }
                await fs.promises.writeFile(targetPath, data);
                componentsRestored++;
            }
            return {
                status: 'success',
                resourceId: targetResourceId,
                restoredAt: new Date(),
                componentsRestored,
            };
        }
        catch (error) {
            return {
                status: 'failed',
                resourceId: targetResourceId,
                restoredAt: new Date(),
                error: error instanceof Error ? error.message : String(error),
                componentsRestored,
            };
        }
    }
    async deleteBackup(backupId) {
        const manifest = this.backups.get(backupId);
        if (!manifest) {
            throw new Error(`Backup ${backupId} not found`);
        }
        manifest.status = 'deleting';
        await this.appendToJsonl(this.manifestFile, JSON.stringify(manifest));
        // Delete backup files
        const backupDir = path.join(this.baseDir, 'backups', backupId);
        if (fs.existsSync(backupDir)) {
            await fs.promises.rm(backupDir, { recursive: true, force: true });
        }
        manifest.status = 'deleted';
        await this.appendToJsonl(this.manifestFile, JSON.stringify(manifest));
        this.backups.delete(backupId);
    }
    async getBackup(backupId) {
        const manifest = this.backups.get(backupId);
        if (!manifest) {
            throw new Error(`Backup ${backupId} not found`);
        }
        return {
            id: manifest.id,
            resourceId: manifest.resourceId,
            resourceType: manifest.resourceType,
            name: manifest.name,
            description: manifest.description,
            status: manifest.status,
            sizeBytes: manifest.sizeBytes,
            createdAt: new Date(manifest.createdAt),
            completedAt: manifest.completedAt ? new Date(manifest.completedAt) : undefined,
            encrypted: manifest.encrypted,
            metadata: manifest.metadata,
        };
    }
    async listBackups(options) {
        let backups = Array.from(this.backups.values());
        // Filter by resource ID
        if (options?.resourceId) {
            backups = backups.filter((b) => b.resourceId === options.resourceId);
        }
        // Filter by resource type
        if (options?.resourceType) {
            backups = backups.filter((b) => b.resourceType === options.resourceType);
        }
        // Filter by status
        if (options?.status) {
            backups = backups.filter((b) => b.status === options.status);
        }
        // Limit results
        if (options?.maxResults) {
            backups = backups.slice(0, options.maxResults);
        }
        return backups.map((manifest) => ({
            id: manifest.id,
            resourceId: manifest.resourceId,
            resourceType: manifest.resourceType,
            name: manifest.name,
            description: manifest.description,
            status: manifest.status,
            sizeBytes: manifest.sizeBytes,
            createdAt: new Date(manifest.createdAt),
            completedAt: manifest.completedAt ? new Date(manifest.completedAt) : undefined,
            encrypted: manifest.encrypted,
            metadata: manifest.metadata,
        }));
    }
    async verifyBackup(backupId) {
        const manifest = this.backups.get(backupId);
        if (!manifest) {
            return {
                status: 'invalid',
                verifiedAt: new Date(),
                error: `Backup ${backupId} not found`,
            };
        }
        const backupDir = path.join(this.baseDir, 'backups', backupId);
        if (!fs.existsSync(backupDir)) {
            return {
                status: 'corrupted',
                verifiedAt: new Date(),
                error: 'Backup directory not found',
            };
        }
        try {
            // Verify manifest checksum (skip if empty, means it's the first version)
            if (manifest.checksum) {
                const expectedChecksum = manifest.checksum;
                const actualChecksum = this.calculateManifestChecksum(manifest);
                if (actualChecksum !== expectedChecksum) {
                    return {
                        status: 'corrupted',
                        verifiedAt: new Date(),
                        error: 'Manifest checksum mismatch',
                    };
                }
            }
            // Verify all files
            for (const file of manifest.files) {
                const filePath = path.join(backupDir, file.path);
                if (!fs.existsSync(filePath)) {
                    return {
                        status: 'corrupted',
                        verifiedAt: new Date(),
                        error: `File not found: ${file.path}`,
                    };
                }
                const data = await fs.promises.readFile(filePath);
                const checksum = this.calculateChecksum(data);
                if (checksum !== file.checksum) {
                    return {
                        status: 'corrupted',
                        verifiedAt: new Date(),
                        error: `Checksum mismatch for file: ${file.path} (expected: ${file.checksum}, got: ${checksum})`,
                        checksum: checksum,
                    };
                }
            }
            return {
                status: 'valid',
                verifiedAt: new Date(),
                checksum: manifest.checksum,
            };
        }
        catch (error) {
            return {
                status: 'corrupted',
                verifiedAt: new Date(),
                error: error instanceof Error ? error.message : String(error),
            };
        }
    }
    async scanResource(resourceId, resourceType) {
        // Simulate scanning resource files
        const resourcePath = this.resolveResourcePath(resourceId, resourceType, '');
        if (!fs.existsSync(resourcePath)) {
            return [];
        }
        const files = [];
        await this.scanDirectory(resourcePath, resourcePath, files);
        return files;
    }
    async scanDirectory(basePath, currentPath, files) {
        const entries = await fs.promises.readdir(currentPath, { withFileTypes: true });
        for (const entry of entries) {
            const fullPath = path.join(currentPath, entry.name);
            const relativePath = path.relative(basePath, fullPath).replace(/\\/g, '/');
            if (entry.isDirectory()) {
                await this.scanDirectory(basePath, fullPath, files);
            }
            else if (entry.isFile()) {
                files.push({ path: relativePath });
            }
        }
    }
    resolveResourcePath(resourceId, resourceType, filePath) {
        // Resolve resource path based on type
        return path.join(this.baseDir, 'resources', resourceType, resourceId, filePath);
    }
    calculateChecksum(data) {
        return crypto.createHash('sha256').update(data).digest('hex');
    }
    calculateManifestChecksum(manifest) {
        const manifestCopy = { ...manifest, checksum: '' };
        const json = JSON.stringify(manifestCopy);
        return crypto.createHash('sha256').update(json).digest('hex');
    }
    loadManifests() {
        if (!fs.existsSync(this.manifestFile)) {
            return;
        }
        const content = fs.readFileSync(this.manifestFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        for (const line of lines) {
            try {
                const manifest = JSON.parse(line);
                // Keep latest manifest for each backup ID
                if (!this.backups.has(manifest.id) || manifest.status !== 'deleted') {
                    this.backups.set(manifest.id, manifest);
                }
            }
            catch (error) {
                // Skip invalid lines
                continue;
            }
        }
    }
    async appendToJsonl(filePath, jsonContent) {
        await this.ensureDirectory(path.dirname(filePath));
        try {
            await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
        }
        catch (error) {
            const err = error;
            if (err.code !== 'EEXIST') {
                throw err;
            }
        }
        const line = `${jsonContent}\n`;
        const handle = await fs.promises.open(filePath, 'a');
        try {
            await handle.write(line);
            await handle.sync();
        }
        finally {
            await handle.close();
        }
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    generateBackupId() {
        return `backup-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
}
exports.LocalBackup = LocalBackup;
//# sourceMappingURL=LocalBackup.js.map