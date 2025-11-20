/**
 * BackupPort
 *
 * Cloud-agnostic interface for backup operations.
 * Implemented by local adapters for data backup and restore.
 *
 * @interface BackupPort
 */
export interface BackupPort {
    /**
     * Create a backup.
     *
     * @param request - Backup creation request
     * @returns Promise resolving to backup information
     */
    createBackup(request: BackupCreateRequest): Promise<Backup>;
    /**
     * Restore from a backup.
     *
     * @param backupId - Backup ID to restore from
     * @param options - Optional restore options
     * @returns Promise resolving to restore result
     */
    restoreBackup(backupId: string, options?: BackupRestoreOptions): Promise<BackupRestoreResult>;
    /**
     * Delete a backup.
     *
     * @param backupId - Backup ID to delete
     * @returns Promise resolving when backup is deleted
     */
    deleteBackup(backupId: string): Promise<void>;
    /**
     * Get backup information.
     *
     * @param backupId - Backup ID
     * @returns Promise resolving to backup information
     */
    getBackup(backupId: string): Promise<Backup>;
    /**
     * List backups.
     *
     * @param options - Optional filter options
     * @returns Promise resolving to list of backups
     */
    listBackups(options?: BackupListOptions): Promise<Backup[]>;
    /**
     * Verify backup integrity.
     *
     * @param backupId - Backup ID to verify
     * @returns Promise resolving to verification result
     */
    verifyBackup(backupId: string): Promise<BackupVerificationResult>;
}
/**
 * Request for creating a backup.
 */
export interface BackupCreateRequest {
    /** Resource identifier to backup */
    resourceId: string;
    /** Resource type */
    resourceType: string;
    /** Backup name */
    name?: string;
    /** Backup description */
    description?: string;
    /** Backup tags/labels */
    tags?: Record<string, string>;
    /** Encryption settings */
    encrypted?: boolean;
}
/**
 * Represents a backup.
 */
export interface Backup {
    /** Backup ID */
    id: string;
    /** Resource identifier that was backed up */
    resourceId: string;
    /** Resource type */
    resourceType: string;
    /** Backup name */
    name?: string;
    /** Backup description */
    description?: string;
    /** Backup status */
    status: 'creating' | 'completed' | 'failed' | 'deleting' | 'deleted';
    /** Backup size in bytes */
    sizeBytes?: number;
    /** Creation timestamp */
    createdAt: Date;
    /** Completion timestamp */
    completedAt?: Date;
    /** Encryption status */
    encrypted: boolean;
    /** Backup metadata */
    metadata?: Record<string, unknown>;
}
/**
 * Options for restoring from a backup.
 */
export interface BackupRestoreOptions {
    /** Target resource identifier (if different from original) */
    targetResourceId?: string;
    /** Whether to overwrite existing resource */
    overwrite?: boolean;
    /** Restore specific components only */
    components?: string[];
}
/**
 * Result of a backup restore operation.
 */
export interface BackupRestoreResult {
    /** Restore status */
    status: 'success' | 'failed' | 'partial';
    /** Restored resource identifier */
    resourceId: string;
    /** Restore timestamp */
    restoredAt: Date;
    /** Error message if restore failed */
    error?: string;
    /** Number of components restored */
    componentsRestored?: number;
}
/**
 * Options for listing backups.
 */
export interface BackupListOptions {
    /** Filter by resource ID */
    resourceId?: string;
    /** Filter by resource type */
    resourceType?: string;
    /** Filter by status */
    status?: Backup['status'];
    /** Maximum number of backups to return */
    maxResults?: number;
}
/**
 * Result of backup verification.
 */
export interface BackupVerificationResult {
    /** Verification status */
    status: 'valid' | 'invalid' | 'corrupted';
    /** Verification timestamp */
    verifiedAt: Date;
    /** Checksum/hash of backup */
    checksum?: string;
    /** Error message if verification failed */
    error?: string;
}
//# sourceMappingURL=BackupPort.d.ts.map