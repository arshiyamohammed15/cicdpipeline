import { BaseStoragePathResolver, StoragePlane } from '../../../shared/storage/BaseStoragePathResolver';

export type { StoragePlane };

/**
 * Storage path resolver that ensures compliance with storage governance rules.
 * All paths must be resolved via ZU_ROOT environment variable (Rule 223).
 */
export class StoragePathResolver extends BaseStoragePathResolver {
    constructor(zuRoot?: string) {
        super(zuRoot ?? process.env.ZU_ROOT ?? '');
    }
}
