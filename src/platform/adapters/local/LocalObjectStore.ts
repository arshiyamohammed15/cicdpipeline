/**
 * LocalObjectStore
 * 
 * Local file-based implementation of ObjectStorePort.
 * Stores objects as files under configured root with metadata sidecar .meta.json.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  ObjectStorePort,
  ObjectStorePutOptions,
  ObjectStorePutResult,
  ObjectStoreGetResult,
  ObjectStoreListOptions,
  ObjectStoreListResult,
} from '../../ports/ObjectStorePort';

interface ObjectMetadata {
  contentType?: string;
  metadata?: Record<string, string>;
  size: number;
  uploadedAt: string;
  etag?: string;
}

export class LocalObjectStore implements ObjectStorePort {
  private rootDir: string;

  constructor(rootDir: string) {
    this.rootDir = rootDir;
  }

  async put(
    bucket: string,
    key: string,
    data: string | Buffer,
    options?: ObjectStorePutOptions
  ): Promise<ObjectStorePutResult> {
    const objectPath = this.getObjectPath(bucket, key);
    const metaPath = this.getMetadataPath(bucket, key);
    await this.ensureDirectory(path.dirname(objectPath));

    const dataBuffer = typeof data === 'string' ? Buffer.from(data, 'utf-8') : data;
    const size = dataBuffer.length;
    const etag = this.generateETag(dataBuffer);
    const uploadedAt = new Date();

    // Write object file
    await fs.promises.writeFile(objectPath, dataBuffer);

    // Write metadata sidecar
    const metadata: ObjectMetadata = {
      contentType: options?.contentType,
      metadata: options?.metadata,
      size,
      uploadedAt: uploadedAt.toISOString(),
      etag,
    };
    await fs.promises.writeFile(metaPath, JSON.stringify(metadata, null, 2));

    return {
      key,
      etag,
      size,
      uploadedAt,
    };
  }

  async get(bucket: string, key: string): Promise<ObjectStoreGetResult> {
    const objectPath = this.getObjectPath(bucket, key);
    const metaPath = this.getMetadataPath(bucket, key);

    if (!fs.existsSync(objectPath)) {
      throw new Error(`Object not found: ${bucket}/${key}`);
    }

    const data = await fs.promises.readFile(objectPath);
    let metadata: ObjectMetadata = {
      size: data.length,
      uploadedAt: new Date().toISOString(),
    };

    if (fs.existsSync(metaPath)) {
      try {
        const metaContent = await fs.promises.readFile(metaPath, 'utf-8');
        metadata = JSON.parse(metaContent);
      } catch (error) {
        // Use default metadata
      }
    }

    const stats = await fs.promises.stat(objectPath);

    return {
      data,
      contentType: metadata.contentType,
      metadata: metadata.metadata,
      size: metadata.size,
      lastModified: stats.mtime,
      etag: metadata.etag,
    };
  }

  async delete(bucket: string, key: string): Promise<void> {
    const objectPath = this.getObjectPath(bucket, key);
    const metaPath = this.getMetadataPath(bucket, key);

    if (fs.existsSync(objectPath)) {
      await fs.promises.unlink(objectPath);
    }

    if (fs.existsSync(metaPath)) {
      await fs.promises.unlink(metaPath);
    }
  }

  async list(
    bucket: string,
    prefix?: string,
    options?: ObjectStoreListOptions
  ): Promise<ObjectStoreListResult> {
    const bucketPath = path.join(this.rootDir, bucket);
    if (!fs.existsSync(bucketPath)) {
      return {
        keys: [],
        isTruncated: false,
      };
    }

    const keys: string[] = [];
    const commonPrefixes: string[] = [];
    const maxKeys = options?.maxKeys || 1000;
    const delimiter = options?.delimiter;

    await this.listRecursive(bucketPath, bucket, prefix || '', delimiter, keys, commonPrefixes, maxKeys);

    return {
      keys: keys.slice(0, maxKeys),
      commonPrefixes: delimiter ? commonPrefixes : undefined,
      isTruncated: keys.length > maxKeys,
    };
  }

  async exists(bucket: string, key: string): Promise<boolean> {
    const objectPath = this.getObjectPath(bucket, key);
    return fs.existsSync(objectPath);
  }

  private getObjectPath(bucket: string, key: string): string {
    return path.join(this.rootDir, bucket, key);
  }

  private getMetadataPath(bucket: string, key: string): string {
    return path.join(this.rootDir, bucket, `${key}.meta.json`);
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private async listRecursive(
    dirPath: string,
    bucket: string,
    prefix: string,
    delimiter: string | undefined,
    keys: string[],
    commonPrefixes: string[],
    maxKeys: number
  ): Promise<void> {
    if (keys.length >= maxKeys) {
      return;
    }

    const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      if (keys.length >= maxKeys) {
        break;
      }

      const fullPath = path.join(dirPath, entry.name);
      const relativePath = path.relative(path.join(this.rootDir, bucket), fullPath).replace(/\\/g, '/');

      // Skip metadata files
      if (entry.name.endsWith('.meta.json')) {
        continue;
      }

      // Filter by prefix
      if (prefix && !relativePath.startsWith(prefix)) {
        continue;
      }

      if (entry.isDirectory()) {
        if (delimiter) {
          const prefixPath = relativePath + delimiter;
          if (!commonPrefixes.includes(prefixPath)) {
            commonPrefixes.push(prefixPath);
          }
        } else {
          await this.listRecursive(fullPath, bucket, prefix, delimiter, keys, commonPrefixes, maxKeys);
        }
      } else if (entry.isFile()) {
        keys.push(relativePath);
      }
    }
  }

  private generateETag(data: Buffer): string {
    // Simple hash-based ETag
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      hash = ((hash << 5) - hash + data[i]) | 0;
    }
    return Math.abs(hash).toString(16);
  }
}

