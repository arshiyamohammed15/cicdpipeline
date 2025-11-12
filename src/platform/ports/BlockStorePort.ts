/**
 * BlockStorePort
 * 
 * Cloud-agnostic interface for block storage operations.
 * Implemented by local adapters for persistent block/volume storage.
 * 
 * @interface BlockStorePort
 */
export interface BlockStorePort {
  /**
   * Create a new block volume.
   * 
   * @param request - Volume creation request
   * @returns Promise resolving to created volume
   */
  createVolume(request: BlockVolumeCreateRequest): Promise<BlockVolume>;

  /**
   * Delete a block volume.
   * 
   * @param volumeId - Volume ID to delete
   * @returns Promise resolving when volume is deleted
   */
  deleteVolume(volumeId: string): Promise<void>;

  /**
   * Attach a volume to an instance.
   * 
   * @param volumeId - Volume ID to attach
   * @param instanceId - Instance ID to attach to
   * @param deviceName - Device name/path for attachment
   * @returns Promise resolving to attachment result
   */
  attachVolume(
    volumeId: string,
    instanceId: string,
    deviceName: string
  ): Promise<BlockVolumeAttachment>;

  /**
   * Detach a volume from an instance.
   * 
   * @param volumeId - Volume ID to detach
   * @param instanceId - Instance ID to detach from
   * @returns Promise resolving when volume is detached
   */
  detachVolume(volumeId: string, instanceId: string): Promise<void>;

  /**
   * Get volume information.
   * 
   * @param volumeId - Volume ID
   * @returns Promise resolving to volume information
   */
  getVolume(volumeId: string): Promise<BlockVolume>;

  /**
   * Create a snapshot of a volume.
   * 
   * @param volumeId - Volume ID to snapshot
   * @param snapshotName - Optional snapshot name
   * @returns Promise resolving to snapshot
   */
  createSnapshot(volumeId: string, snapshotName?: string): Promise<BlockSnapshot>;
}

/**
 * Request for creating a block volume.
 */
export interface BlockVolumeCreateRequest {
  /** Volume size in GB */
  sizeGB: number;
  /** Volume type/performance tier */
  volumeType?: string;
  /** Availability zone/region */
  availabilityZone?: string;
  /** Encryption settings */
  encrypted?: boolean;
  /** Volume tags/labels */
  tags?: Record<string, string>;
}

/**
 * Represents a block volume.
 */
export interface BlockVolume {
  /** Volume ID */
  id: string;
  /** Volume size in GB */
  sizeGB: number;
  /** Volume type */
  type: string;
  /** Current status */
  status: 'creating' | 'available' | 'in-use' | 'deleting' | 'deleted' | 'error';
  /** Availability zone */
  availabilityZone?: string;
  /** Encryption status */
  encrypted: boolean;
  /** Creation timestamp */
  createdAt: Date;
  /** Attached instances */
  attachments?: BlockVolumeAttachment[];
}

/**
 * Represents a volume attachment to an instance.
 */
export interface BlockVolumeAttachment {
  /** Volume ID */
  volumeId: string;
  /** Instance ID */
  instanceId: string;
  /** Device name/path */
  deviceName: string;
  /** Attachment status */
  status: 'attaching' | 'attached' | 'detaching' | 'detached' | 'error';
  /** Attachment timestamp */
  attachedAt?: Date;
}

/**
 * Represents a volume snapshot.
 */
export interface BlockSnapshot {
  /** Snapshot ID */
  id: string;
  /** Source volume ID */
  volumeId: string;
  /** Snapshot size in GB */
  sizeGB: number;
  /** Snapshot status */
  status: 'pending' | 'completed' | 'error';
  /** Creation timestamp */
  createdAt: Date;
  /** Snapshot name */
  name?: string;
}

