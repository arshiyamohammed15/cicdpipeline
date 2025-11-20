"use strict";
/**
 * LocalBlockStore
 *
 * Local file-based implementation of BlockStorePort.
 * Uses append-only storage with fsync for persistence.
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
exports.LocalBlockStore = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalBlockStore {
    constructor(baseDir) {
        this.volumes = new Map();
        this.baseDir = baseDir;
        this.volumesFile = path.join(baseDir, 'volumes.jsonl');
        this.loadVolumes();
    }
    async createVolume(request) {
        const volumeId = this.generateVolumeId();
        const now = new Date();
        const record = {
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
    async deleteVolume(volumeId) {
        const volume = this.volumes.get(volumeId);
        if (!volume) {
            throw new Error(`Volume ${volumeId} not found`);
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
    async attachVolume(volumeId, instanceId, deviceName) {
        const volume = this.volumes.get(volumeId);
        if (!volume) {
            throw new Error(`Volume ${volumeId} not found`);
        }
        if (volume.status !== 'available') {
            throw new Error(`Volume ${volumeId} is not available`);
        }
        const attachment = {
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
    async detachVolume(volumeId, instanceId) {
        const volume = this.volumes.get(volumeId);
        if (!volume) {
            throw new Error(`Volume ${volumeId} not found`);
        }
        const attachmentIndex = volume.attachments.findIndex((att) => att.instanceId === instanceId);
        if (attachmentIndex === -1) {
            throw new Error(`Volume ${volumeId} is not attached to instance ${instanceId}`);
        }
        volume.attachments[attachmentIndex].status = 'detaching';
        await this.updateVolume(volumeId, volume);
        volume.attachments.splice(attachmentIndex, 1);
        volume.status = volume.attachments.length > 0 ? 'in-use' : 'available';
        await this.updateVolume(volumeId, volume);
    }
    async getVolume(volumeId) {
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
            attachments: volume.attachments,
        };
    }
    async createSnapshot(volumeId, snapshotName) {
        const volume = this.volumes.get(volumeId);
        if (!volume) {
            throw new Error(`Volume ${volumeId} not found`);
        }
        const snapshotId = this.generateSnapshotId();
        const now = new Date();
        const snapshot = {
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
    loadVolumes() {
        if (!fs.existsSync(this.volumesFile)) {
            return;
        }
        const content = fs.readFileSync(this.volumesFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
                // Keep latest record for each volume ID
                if (!this.volumes.has(record.id) || record.status !== 'deleted') {
                    this.volumes.set(record.id, record);
                }
            }
            catch (error) {
                // Skip invalid lines
                continue;
            }
        }
    }
    async updateVolume(volumeId, record) {
        // Append updated record (append-only)
        await this.appendToJsonl(this.volumesFile, JSON.stringify(record));
        this.volumes.set(volumeId, record);
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
            await handle.sync(); // fsync for append-only guarantee
        }
        finally {
            await handle.close();
        }
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    generateVolumeId() {
        return `vol-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    generateSnapshotId() {
        return `snap-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
}
exports.LocalBlockStore = LocalBlockStore;
//# sourceMappingURL=LocalBlockStore.js.map