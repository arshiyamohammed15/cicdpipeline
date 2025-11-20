/**
 * LocalBlockStore
 *
 * Local file-based implementation of BlockStorePort.
 * Uses append-only storage with fsync for persistence.
 */
import { BlockStorePort, BlockVolumeCreateRequest, BlockVolume, BlockVolumeAttachment, BlockSnapshot } from '../../ports/BlockStorePort';
export declare class LocalBlockStore implements BlockStorePort {
    private baseDir;
    private volumesFile;
    private volumes;
    constructor(baseDir: string);
    createVolume(request: BlockVolumeCreateRequest): Promise<BlockVolume>;
    deleteVolume(volumeId: string): Promise<void>;
    attachVolume(volumeId: string, instanceId: string, deviceName: string): Promise<BlockVolumeAttachment>;
    detachVolume(volumeId: string, instanceId: string): Promise<void>;
    getVolume(volumeId: string): Promise<BlockVolume>;
    createSnapshot(volumeId: string, snapshotName?: string): Promise<BlockSnapshot>;
    private loadVolumes;
    private updateVolume;
    private appendToJsonl;
    private ensureDirectory;
    private generateVolumeId;
    private generateSnapshotId;
}
//# sourceMappingURL=LocalBlockStore.d.ts.map