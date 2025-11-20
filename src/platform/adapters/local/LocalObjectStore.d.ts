/**
 * LocalObjectStore
 *
 * Local file-based implementation of ObjectStorePort.
 * Stores objects as files under configured root with metadata sidecar .meta.json.
 */
/// <reference types="node" />
/// <reference types="node" />
import { ObjectStorePort, ObjectStorePutOptions, ObjectStorePutResult, ObjectStoreGetResult, ObjectStoreListOptions, ObjectStoreListResult } from '../../ports/ObjectStorePort';
export declare class LocalObjectStore implements ObjectStorePort {
    private rootDir;
    constructor(rootDir: string);
    put(bucket: string, key: string, data: string | Buffer, options?: ObjectStorePutOptions): Promise<ObjectStorePutResult>;
    get(bucket: string, key: string): Promise<ObjectStoreGetResult>;
    delete(bucket: string, key: string): Promise<void>;
    list(bucket: string, prefix?: string, options?: ObjectStoreListOptions): Promise<ObjectStoreListResult>;
    exists(bucket: string, key: string): Promise<boolean>;
    private getObjectPath;
    private getMetadataPath;
    private ensureDirectory;
    private listRecursive;
    private generateETag;
}
//# sourceMappingURL=LocalObjectStore.d.ts.map