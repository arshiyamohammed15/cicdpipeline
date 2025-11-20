"use strict";
/**
 * LocalObjectStore
 *
 * Local file-based implementation of ObjectStorePort.
 * Stores objects as files under configured root with metadata sidecar .meta.json.
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
exports.LocalObjectStore = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalObjectStore {
    constructor(rootDir) {
        this.rootDir = rootDir;
    }
    async put(bucket, key, data, options) {
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
        const metadata = {
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
    async get(bucket, key) {
        const objectPath = this.getObjectPath(bucket, key);
        const metaPath = this.getMetadataPath(bucket, key);
        if (!fs.existsSync(objectPath)) {
            throw new Error(`Object not found: ${bucket}/${key}`);
        }
        const data = await fs.promises.readFile(objectPath);
        let metadata = {
            size: data.length,
            uploadedAt: new Date().toISOString(),
        };
        if (fs.existsSync(metaPath)) {
            try {
                const metaContent = await fs.promises.readFile(metaPath, 'utf-8');
                metadata = JSON.parse(metaContent);
            }
            catch (error) {
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
    async delete(bucket, key) {
        const objectPath = this.getObjectPath(bucket, key);
        const metaPath = this.getMetadataPath(bucket, key);
        if (fs.existsSync(objectPath)) {
            await fs.promises.unlink(objectPath);
        }
        if (fs.existsSync(metaPath)) {
            await fs.promises.unlink(metaPath);
        }
    }
    async list(bucket, prefix, options) {
        const bucketPath = path.join(this.rootDir, bucket);
        if (!fs.existsSync(bucketPath)) {
            return {
                keys: [],
                isTruncated: false,
            };
        }
        const keys = [];
        const commonPrefixes = [];
        const maxKeys = options?.maxKeys || 1000;
        const delimiter = options?.delimiter;
        await this.listRecursive(bucketPath, bucket, prefix || '', delimiter, keys, commonPrefixes, maxKeys);
        return {
            keys: keys.slice(0, maxKeys),
            commonPrefixes: delimiter ? commonPrefixes : undefined,
            isTruncated: keys.length > maxKeys,
        };
    }
    async exists(bucket, key) {
        const objectPath = this.getObjectPath(bucket, key);
        return fs.existsSync(objectPath);
    }
    getObjectPath(bucket, key) {
        return path.join(this.rootDir, bucket, key);
    }
    getMetadataPath(bucket, key) {
        return path.join(this.rootDir, bucket, `${key}.meta.json`);
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    async listRecursive(dirPath, bucket, prefix, delimiter, keys, commonPrefixes, maxKeys) {
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
                }
                else {
                    await this.listRecursive(fullPath, bucket, prefix, delimiter, keys, commonPrefixes, maxKeys);
                }
            }
            else if (entry.isFile()) {
                keys.push(relativePath);
            }
        }
    }
    generateETag(data) {
        // Simple hash-based ETag
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            hash = ((hash << 5) - hash + data[i]) | 0;
        }
        return Math.abs(hash).toString(16);
    }
}
exports.LocalObjectStore = LocalObjectStore;
//# sourceMappingURL=LocalObjectStore.js.map