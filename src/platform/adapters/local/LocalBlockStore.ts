/**
 * LocalBlockStore
 *
 * Local file-based implementation of BlockStorePort.
 * Uses append-only storage with fsync for persistence.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  BlockStorePort,
  BlockVolumeCreateRequest,
  BlockVolume,
  BlockVolumeAttachment,
  BlockSnapshot,
} from '../../ports/BlockStorePort';

interface VolumeRecord {
  id: string;
  sizeGB: number;
  type: string;
  status: BlockVolume['status'];
  availabilityZone?: string;
  encrypted: boolean;
  createdAt: string;
  attachments: BlockVolumeAttachment[];
}

export class LocalBlockStore implements BlockStorePort {
  private baseDir: string;
  private volumesFile: string;
  private volumes: Map<string, VolumeRecord> = new Map();

  constructor(baseDir: string) {
    this.baseDir = baseDir;
    this.volumesFile = path.join(baseDir, 'volumes.jsonl');
    this.loadVolumes();
  }

  async createVolume(request: BlockVolumeCreateRequest): Promise<BlockVolume> {
    const volumeId = this.generateVolumeId();
    const now = new Date();

    const record: VolumeRecord = {
      id: volumeId,
      sizeGB: request.sizeGB,
      type: request.volumeType || 'standard',
      status: 'creating',
      availabilityZone: request.availabilityZone,
      encrypted: request.encrypted || false,
      createdAt: now.toISOString(),
      attachments: [],
    };

    // Append to volumes file (append-only)
    await this.appendToJsonl(this.volumesFile, JSON.stringify(record));

    // Update status to available
    record.status = 'available';
    await this.updateVolume(volumeId, record);

    this.volumes.set(volumeId, record);

    return {
      id: volumeId,
      sizeGB: request.sizeGB,
      type: record.type,
      status: 'available',
      availabilityZone: request.availabilityZone,
      encrypted: record.encrypted,
      createdAt: now,
      attachments: [],
    };
  }

  async deleteVolume(volumeId: string): Promise<void> {
    const volume = this.volumes.get(volumeId);
    if (!volume) {
      throw new Error(`Volume ${volumeId} not found`);
    }

    // Ensure attachments is initialized
    if (!volume.attachments) {
      volume.attachments = [];
    }

    if (volume.attachments.length > 0) {
      throw new Error(`Cannot delete volume ${volumeId}: volume is attached`);
    }

    volume.status = 'deleting';
    await this.updateVolume(volumeId, volume);

    // Create deletion record (append-only)
    const deleteRecord = {
      ...volume,
      status: 'deleted',
      deletedAt: new Date().toISOString(),
    };
    await this.appendToJsonl(this.volumesFile, JSON.stringify(deleteRecord));

    this.volumes.delete(volumeId);
  }

  async attachVolume(
    volumeId: string,
    instanceId: string,
    deviceName: string
  ): Promise<BlockVolumeAttachment> {
    const volume = this.volumes.get(volumeId);
    if (!volume) {
      throw new Error(`Volume ${volumeId} not found`);
    }

    if (volume.status !== 'available') {
      throw new Error(`Volume ${volumeId} is not available`);
    }

    // Ensure attachments is initialized
    if (!volume.attachments) {
      volume.attachments = [];
    }

    const attachment: BlockVolumeAttachment = {
      volumeId,
      instanceId,
      deviceName,
      status: 'attaching',
    };

    volume.attachments.push(attachment);
    volume.status = 'in-use';
    attachment.status = 'attached';
    attachment.attachedAt = new Date();

    await this.updateVolume(volumeId, volume);

    return attachment;
  }

  async detachVolume(volumeId: string, instanceId: string): Promise<void> {
    const volume = this.volumes.get(volumeId);
    if (!volume) {
      throw new Error(`Volume ${volumeId} not found`);
    }

    // Ensure attachments is initialized
    if (!volume.attachments) {
      volume.attachments = [];
    }

    const attachmentIndex = volume.attachments.findIndex(
      (att) => att.instanceId === instanceId
    );

    if (attachmentIndex === -1) {
      throw new Error(`Volume ${volumeId} is not attached to instance ${instanceId}`);
    }

    volume.attachments[attachmentIndex].status = 'detaching';
    await this.updateVolume(volumeId, volume);

    volume.attachments.splice(attachmentIndex, 1);
    volume.status = volume.attachments.length > 0 ? 'in-use' : 'available';

    await this.updateVolume(volumeId, volume);
  }

  async getVolume(volumeId: string): Promise<BlockVolume> {
    const volume = this.volumes.get(volumeId);
    if (!volume) {
      throw new Error(`Volume ${volumeId} not found`);
    }

    return {
      id: volume.id,
      sizeGB: volume.sizeGB,
      type: volume.type,
      status: volume.status,
      availabilityZone: volume.availabilityZone,
      encrypted: volume.encrypted,
      createdAt: new Date(volume.createdAt),
      attachments: volume.attachments || [],
    };
  }

  async createSnapshot(volumeId: string, snapshotName?: string): Promise<BlockSnapshot> {
    const volume = this.volumes.get(volumeId);
    if (!volume) {
      throw new Error(`Volume ${volumeId} not found`);
    }

    const snapshotId = this.generateSnapshotId();
    const now = new Date();

    const snapshot: BlockSnapshot = {
      id: snapshotId,
      volumeId,
      sizeGB: volume.sizeGB,
      status: 'pending',
      createdAt: now,
      name: snapshotName,
    };

    // Append snapshot record (append-only)
    const snapshotFile = path.join(this.baseDir, 'snapshots.jsonl');
    await this.appendToJsonl(snapshotFile, JSON.stringify({
      ...snapshot,
      status: 'completed',
      createdAt: snapshot.createdAt.toISOString(),
    }));

    snapshot.status = 'completed';
    return snapshot;
  }

  private loadVolumes(): void {
    if (!fs.existsSync(this.volumesFile)) {
      return;
    }

    const content = fs.readFileSync(this.volumesFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());

    for (const line of lines) {
      try {
        const record: VolumeRecord = JSON.parse(line);
        // Ensure attachments is always initialized as an array
        if (!record.attachments) {
          record.attachments = [];
        }
        // Keep latest record for each volume ID
        if (!this.volumes.has(record.id) || record.status !== 'deleted') {
          this.volumes.set(record.id, record);
        }
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }
  }

  private async updateVolume(volumeId: string, record: VolumeRecord): Promise<void> {
    // Append updated record (append-only)
    await this.appendToJsonl(this.volumesFile, JSON.stringify(record));
    this.volumes.set(volumeId, record);
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
      await handle.sync(); // fsync for append-only guarantee
    } finally {
      await handle.close();
    }
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private generateVolumeId(): string {
    return `vol-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private generateSnapshotId(): string {
    return `snap-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }
}
