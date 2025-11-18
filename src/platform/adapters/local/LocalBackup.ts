/**
 * LocalBackup
 *
 * Local file-based implementation of BackupPort.
 * Uses incremental snapshot manifest + checksums with verify routine.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import {
  BackupPort,
  BackupCreateRequest,
  Backup,
  BackupRestoreOptions,
  BackupRestoreResult,
  BackupListOptions,
  BackupVerificationResult,
} from '../../ports/BackupPort';

interface BackupManifest {
  id: string;
  resourceId: string;
  resourceType: string;
  name?: string;
  description?: string;
  status: Backup['status'];
  sizeBytes?: number;
  createdAt: string;
  completedAt?: string;
  encrypted: boolean;
  metadata?: Record<string, unknown>;
  checksum: string;
  files: BackupFile[];
}

interface BackupFile {
  path: string;
  checksum: string;
  size: number;
  incremental: boolean;
  baseBackupId?: string; // For incremental backups
}

export class LocalBackup implements BackupPort {
  private baseDir: string;
  private manifestFile: string;
  private backups: Map<string, BackupManifest> = new Map();

  constructor(baseDir: string) {
    this.baseDir = baseDir;
    this.manifestFile = path.join(baseDir, 'backup-manifest.jsonl');
    this.loadManifests();
  }

  async createBackup(request: BackupCreateRequest): Promise<Backup> {
    const backupId = this.generateBackupId();
    const now = new Date();
    const backupDir = path.join(this.baseDir, 'backups', backupId);

    await this.ensureDirectory(backupDir);

    const manifest: BackupManifest = {
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
    } catch (error) {
      manifest.status = 'failed';
      await this.appendToJsonl(this.manifestFile, JSON.stringify(manifest));
      throw error;
    }
  }

  async restoreBackup(backupId: string, options?: BackupRestoreOptions): Promise<BackupRestoreResult> {
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
    } catch (error) {
      return {
        status: 'failed',
        resourceId: targetResourceId,
        restoredAt: new Date(),
        error: error instanceof Error ? error.message : String(error),
        componentsRestored,
      };
    }
  }

  async deleteBackup(backupId: string): Promise<void> {
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

  async getBackup(backupId: string): Promise<Backup> {
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

  async listBackups(options?: BackupListOptions): Promise<Backup[]> {
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

  async verifyBackup(backupId: string): Promise<BackupVerificationResult> {
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
    } catch (error) {
      return {
        status: 'corrupted',
        verifiedAt: new Date(),
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  private async scanResource(resourceId: string, resourceType: string): Promise<Array<{ path: string }>> {
    // Simulate scanning resource files
    const resourcePath = this.resolveResourcePath(resourceId, resourceType, '');
    if (!fs.existsSync(resourcePath)) {
      return [];
    }

    const files: Array<{ path: string }> = [];
    await this.scanDirectory(resourcePath, resourcePath, files);
    return files;
  }

  private async scanDirectory(
    basePath: string,
    currentPath: string,
    files: Array<{ path: string }>
  ): Promise<void> {
    const entries = await fs.promises.readdir(currentPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);
      const relativePath = path.relative(basePath, fullPath).replace(/\\/g, '/');

      if (entry.isDirectory()) {
        await this.scanDirectory(basePath, fullPath, files);
      } else if (entry.isFile()) {
        files.push({ path: relativePath });
      }
    }
  }

  private resolveResourcePath(resourceId: string, resourceType: string, filePath: string): string {
    // Resolve resource path based on type
    return path.join(this.baseDir, 'resources', resourceType, resourceId, filePath);
  }

  private calculateChecksum(data: Buffer): string {
    return crypto.createHash('sha256').update(data).digest('hex');
  }

  private calculateManifestChecksum(manifest: BackupManifest): string {
    const manifestCopy = { ...manifest, checksum: '' };
    const json = JSON.stringify(manifestCopy);
    return crypto.createHash('sha256').update(json).digest('hex');
  }

  private loadManifests(): void {
    if (!fs.existsSync(this.manifestFile)) {
      return;
    }

    const content = fs.readFileSync(this.manifestFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());

    for (const line of lines) {
      try {
        const manifest: BackupManifest = JSON.parse(line);
        // Keep latest manifest for each backup ID
        if (!this.backups.has(manifest.id) || manifest.status !== 'deleted') {
          this.backups.set(manifest.id, manifest);
        }
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }
  }

  private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
    await this.ensureDirectory(path.dirname(filePath));

    try {
      await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== 'EEXIST') {
        throw err;
      }
    }

    const line = `${jsonContent}\n`;
    const handle = await fs.promises.open(filePath, 'a');
    try {
      await handle.write(line);
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private generateBackupId(): string {
    return `backup-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }
}
