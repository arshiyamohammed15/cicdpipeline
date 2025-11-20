/**
 * LocalBackup
 *
 * Local file-based implementation of BackupPort.
 * Uses incremental snapshot manifest + checksums with verify routine.
 */
import { BackupPort, BackupCreateRequest, Backup, BackupRestoreOptions, BackupRestoreResult, BackupListOptions, BackupVerificationResult } from '../../ports/BackupPort';
export declare class LocalBackup implements BackupPort {
    private baseDir;
    private manifestFile;
    private backups;
    constructor(baseDir: string);
    createBackup(request: BackupCreateRequest): Promise<Backup>;
    restoreBackup(backupId: string, options?: BackupRestoreOptions): Promise<BackupRestoreResult>;
    deleteBackup(backupId: string): Promise<void>;
    getBackup(backupId: string): Promise<Backup>;
    listBackups(options?: BackupListOptions): Promise<Backup[]>;
    verifyBackup(backupId: string): Promise<BackupVerificationResult>;
    private scanResource;
    private scanDirectory;
    private resolveResourcePath;
    private calculateChecksum;
    private calculateManifestChecksum;
    private loadManifests;
    private appendToJsonl;
    private ensureDirectory;
    private generateBackupId;
}
//# sourceMappingURL=LocalBackup.d.ts.map