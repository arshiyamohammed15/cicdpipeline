/**
 * ObjectStorePort
 * 
 * Cloud-agnostic interface for object storage operations.
 * Implemented by local adapters for blob/object storage.
 * 
 * @interface ObjectStorePort
 */
export interface ObjectStorePort {
  /**
   * Upload an object to storage.
   * 
   * @param bucket - Bucket/container name
   * @param key - Object key/path
   * @param data - Object data
   * @param options - Optional upload options (content type, metadata, etc.)
   * @returns Promise resolving to upload result
   */
  put(
    bucket: string,
    key: string,
    data: string | Buffer,
    options?: ObjectStorePutOptions
  ): Promise<ObjectStorePutResult>;

  /**
   * Download an object from storage.
   * 
   * @param bucket - Bucket/container name
   * @param key - Object key/path
   * @returns Promise resolving to object data
   */
  get(bucket: string, key: string): Promise<ObjectStoreGetResult>;

  /**
   * Delete an object from storage.
   * 
   * @param bucket - Bucket/container name
   * @param key - Object key/path
   * @returns Promise resolving when object is deleted
   */
  delete(bucket: string, key: string): Promise<void>;

  /**
   * List objects in a bucket/container.
   * 
   * @param bucket - Bucket/container name
   * @param prefix - Optional key prefix filter
   * @param options - Optional list options (max keys, continuation token, etc.)
   * @returns Promise resolving to list of objects
   */
  list(
    bucket: string,
    prefix?: string,
    options?: ObjectStoreListOptions
  ): Promise<ObjectStoreListResult>;

  /**
   * Check if an object exists.
   * 
   * @param bucket - Bucket/container name
   * @param key - Object key/path
   * @returns Promise resolving to true if object exists
   */
  exists(bucket: string, key: string): Promise<boolean>;
}

/**
 * Options for uploading an object.
 */
export interface ObjectStorePutOptions {
  /** Content type/MIME type */
  contentType?: string;
  /** Object metadata */
  metadata?: Record<string, string>;
  /** Encryption settings */
  encryption?: 'none' | 'server-side';
  /** Access control settings */
  acl?: 'private' | 'public-read' | 'public-read-write';
}

/**
 * Result of uploading an object.
 */
export interface ObjectStorePutResult {
  /** Object key/path */
  key: string;
  /** Object ETag/version */
  etag?: string;
  /** Object size in bytes */
  size: number;
  /** Upload timestamp */
  uploadedAt: Date;
}

/**
 * Result of downloading an object.
 */
export interface ObjectStoreGetResult {
  /** Object data */
  data: string | Buffer;
  /** Content type/MIME type */
  contentType?: string;
  /** Object metadata */
  metadata?: Record<string, string>;
  /** Object size in bytes */
  size: number;
  /** Last modified timestamp */
  lastModified?: Date;
  /** Object ETag/version */
  etag?: string;
}

/**
 * Options for listing objects.
 */
export interface ObjectStoreListOptions {
  /** Maximum number of objects to return */
  maxKeys?: number;
  /** Continuation token for pagination */
  continuationToken?: string;
  /** Delimiter for prefix grouping */
  delimiter?: string;
}

/**
 * Result of listing objects.
 */
export interface ObjectStoreListResult {
  /** List of object keys */
  keys: string[];
  /** Common prefixes (for delimiter-based grouping) */
  commonPrefixes?: string[];
  /** Continuation token for next page */
  continuationToken?: string;
  /** Whether more results are available */
  isTruncated: boolean;
}

