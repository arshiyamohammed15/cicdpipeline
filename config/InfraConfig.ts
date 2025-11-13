/**
 * InfraConfig.ts
 *
 * Infrastructure configuration loader with strict precedence and vendor-neutral validation.
 *
 * Precedence: defaults (top-level infra) → per-env "infra" override → optional policy overlay
 *
 * Constraints:
 * - No JSON-Schema engine (internal type-guards only)
 * - No placeholder interpolation
 * - Vendor-neutral validation for neutral infra fields only
 * - Returns frozen config object
 */

import * as fs from 'fs';
import * as path from 'path';

// Type definitions aligned to schema
export interface InfraCompute {
  min_baseline: number;
  allow_spot: boolean;
}

export interface InfraRouting {
  default: 'serverless' | 'gpu-queue' | 'batch';
  cost_profiles: Array<'light' | 'ai-inference' | 'batch'>;
}

export interface InfraStorage {
  object_root: string;
  backups_root: string;
  encryption_at_rest: boolean;
}

export interface InfraNetwork {
  tls_required: boolean;
}

export interface InfraObservability {
  enable_metrics: boolean;
  enable_cost: boolean;
}

export interface InfraDR {
  cross_zone: boolean;
  backup_interval_min: number;
}

export interface InfraFeatureFlags {
  infra_enabled: boolean;
  local_adapters_enabled: boolean;
}

export interface InfraConfig {
  compute: InfraCompute;
  routing: InfraRouting;
  storage: InfraStorage;
  network: InfraNetwork;
  observability: InfraObservability;
  dr: InfraDR;
  feature_flags: InfraFeatureFlags;
}

export interface InfraConfigResult {
  config: Readonly<InfraConfig>;
  isEnabled: boolean;
}

export interface LoadInfraConfigOptions {
  policyOverlayPath?: string;
}

// Vendor identifiers to detect
const VENDOR_IDENTIFIERS = ['aws', 's3', 'azure', 'gcs', 'kms', 'arn'];

/**
 * Deep freeze an object recursively
 */
function deepFreeze<T>(obj: T): Readonly<T> {
  Object.freeze(obj);
  if (obj === null || obj === undefined) {
    return obj;
  }
  Object.getOwnPropertyNames(obj).forEach((prop) => {
    if (
      obj[prop as keyof T] !== null &&
      typeof obj[prop as keyof T] === 'object' &&
      !Object.isFrozen(obj[prop as keyof T])
    ) {
      deepFreeze(obj[prop as keyof T]);
    }
  });
  return obj;
}

/**
 * Type guard: Check if value is a valid integer >= 0
 */
function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}

/**
 * Type guard: Check if value is a boolean
 */
function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean';
}

/**
 * Type guard: Check if value is a string
 */
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

/**
 * Type guard: Check if value is a valid routing default
 */
function isRoutingDefault(value: unknown): value is 'serverless' | 'gpu-queue' | 'batch' {
  return value === 'serverless' || value === 'gpu-queue' || value === 'batch';
}

/**
 * Type guard: Check if value is a valid cost profile
 */
function isCostProfile(value: unknown): value is 'light' | 'ai-inference' | 'batch' {
  return value === 'light' || value === 'ai-inference' || value === 'batch';
}

/**
 * Type guard: Check if value is an array of cost profiles
 */
function isCostProfilesArray(value: unknown): value is Array<'light' | 'ai-inference' | 'batch'> {
  if (!Array.isArray(value)) {
    return false;
  }
  return value.every(isCostProfile);
}

/**
 * Type guard: Validate InfraCompute
 */
function isValidCompute(value: unknown): value is InfraCompute {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isNonNegativeInteger(obj.min_baseline) &&
    isBoolean(obj.allow_spot) &&
    Object.keys(obj).length === 2
  );
}

/**
 * Type guard: Validate InfraRouting
 */
function isValidRouting(value: unknown): value is InfraRouting {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isRoutingDefault(obj.default) &&
    isCostProfilesArray(obj.cost_profiles) &&
    Object.keys(obj).length === 2
  );
}

/**
 * Type guard: Validate InfraStorage
 */
function isValidStorage(value: unknown): value is InfraStorage {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isString(obj.object_root) &&
    isString(obj.backups_root) &&
    isBoolean(obj.encryption_at_rest) &&
    Object.keys(obj).length === 3
  );
}

/**
 * Type guard: Validate InfraNetwork
 */
function isValidNetwork(value: unknown): value is InfraNetwork {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return isBoolean(obj.tls_required) && Object.keys(obj).length === 1;
}

/**
 * Type guard: Validate InfraObservability
 */
function isValidObservability(value: unknown): value is InfraObservability {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isBoolean(obj.enable_metrics) &&
    isBoolean(obj.enable_cost) &&
    Object.keys(obj).length === 2
  );
}

/**
 * Type guard: Validate InfraDR
 */
function isValidDR(value: unknown): value is InfraDR {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isBoolean(obj.cross_zone) &&
    isNonNegativeInteger(obj.backup_interval_min) &&
    Object.keys(obj).length === 2
  );
}

/**
 * Type guard: Validate InfraFeatureFlags
 */
function isValidFeatureFlags(value: unknown): value is InfraFeatureFlags {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isBoolean(obj.infra_enabled) &&
    isBoolean(obj.local_adapters_enabled) &&
    Object.keys(obj).length === 2
  );
}

/**
 * Type guard: Validate complete InfraConfig
 */
function isValidInfraConfig(value: unknown): value is InfraConfig {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const obj = value as Record<string, unknown>;
  return (
    isValidCompute(obj.compute) &&
    isValidRouting(obj.routing) &&
    isValidStorage(obj.storage) &&
    isValidNetwork(obj.network) &&
    isValidObservability(obj.observability) &&
    isValidDR(obj.dr) &&
    isValidFeatureFlags(obj.feature_flags) &&
    Object.keys(obj).length === 7
  );
}

/**
 * Deep merge two objects, with source overriding target
 */
function deepMerge(target: InfraConfig, source: Partial<InfraConfig>): InfraConfig {
  const result: InfraConfig = {
    compute: { ...target.compute, ...(source.compute || {}) },
    routing: { ...target.routing, ...(source.routing || {}) },
    storage: { ...target.storage, ...(source.storage || {}) },
    network: { ...target.network, ...(source.network || {}) },
    observability: { ...target.observability, ...(source.observability || {}) },
    dr: { ...target.dr, ...(source.dr || {}) },
    feature_flags: { ...target.feature_flags, ...(source.feature_flags || {}) },
  };
  return result;
}

/**
 * Recursively scan object for vendor identifiers in string values
 * Returns path to first offending key found, or null if none
 */
function scanForVendorIdentifiers(
  obj: unknown,
  pathPrefix: string = ''
): string | null {
  if (obj === null || obj === undefined) {
    return null;
  }

  if (typeof obj === 'string') {
    const lowerStr = obj.toLowerCase();
    for (const vendor of VENDOR_IDENTIFIERS) {
      if (lowerStr.includes(vendor.toLowerCase())) {
        return pathPrefix || 'root';
      }
    }
    return null;
  }

  if (Array.isArray(obj)) {
    for (let i = 0; i < obj.length; i++) {
      const result = scanForVendorIdentifiers(obj[i], `${pathPrefix}[${i}]`);
      if (result !== null) {
        return result;
      }
    }
    return null;
  }

  if (typeof obj === 'object') {
    for (const key in obj) {
      const currentPath = pathPrefix ? `${pathPrefix}.${key}` : key;
      const result = scanForVendorIdentifiers(
        (obj as Record<string, unknown>)[key],
        currentPath
      );
      if (result !== null) {
        return result;
      }
    }
    return null;
  }

  return null;
}

/**
 * Check if infra config is vendor-neutral by scanning only neutral fields
 * Throws with offending key path if vendor identifier found
 */
export function isVendorNeutral(infra: InfraConfig): void {
  const neutralFields: Array<keyof InfraConfig> = [
    'compute',
    'routing',
    'storage',
    'network',
    'observability',
    'dr',
    'feature_flags',
  ];

  for (const field of neutralFields) {
    const offendingPath = scanForVendorIdentifiers(infra[field], field);
    if (offendingPath !== null) {
      throw new Error(
        `Vendor identifier detected in neutral infra field: ${offendingPath}`
      );
    }
  }
}

/**
 * Load and merge infrastructure configuration with precedence:
 * defaults (top-level infra) → per-env "infra" override → optional policy overlay
 */
export function loadInfraConfig(
  envName: string,
  opts?: LoadInfraConfigOptions
): InfraConfigResult {
  // Resolve paths relative to this file's directory
  // In CommonJS, __dirname is available; in ES modules, use import.meta.url
  // For compatibility, resolve from process.cwd() assuming config/ is at repo root
  const repoRoot = process.cwd();
  const environmentsPath = path.join(
    repoRoot,
    'storage-scripts',
    'config',
    'environments.json'
  );
  const schemaPath = path.join(repoRoot, 'config', 'infra.config.schema.json');

  // Verify schema file exists (reference documentation only, not used for validation)
  if (!fs.existsSync(schemaPath)) {
    throw new Error(`infra.config.schema.json not found at: ${schemaPath}`);
  }

  // Verify schema is valid JSON (but don't use it for validation - type-guards only)
  try {
    const schemaContent = fs.readFileSync(schemaPath, 'utf-8');
    JSON.parse(schemaContent);
  } catch (error) {
    throw new Error(`infra.config.schema.json is invalid JSON: ${error}`);
  }

  // Read environments.json
  if (!fs.existsSync(environmentsPath)) {
    throw new Error(`environments.json not found at: ${environmentsPath}`);
  }

  const environmentsContent = fs.readFileSync(environmentsPath, 'utf-8');
  let environmentsData: {
    infra?: unknown;
    environments?: Record<string, { infra?: unknown }>;
  };

  try {
    environmentsData = JSON.parse(environmentsContent);
  } catch (error) {
    throw new Error(`Failed to parse environments.json: ${error}`);
  }

  // Extract defaults (top-level infra)
  if (!environmentsData.infra) {
    throw new Error('Top-level "infra" block not found in environments.json');
  }

  if (!isValidInfraConfig(environmentsData.infra)) {
    throw new Error('Top-level "infra" block is invalid');
  }

  let config: InfraConfig = { ...environmentsData.infra };

  // Apply per-environment override
  if (environmentsData.environments && environmentsData.environments[envName]) {
    const envData = environmentsData.environments[envName];
    if (envData.infra && typeof envData.infra === 'object' && envData.infra !== null) {
      const envOverride = envData.infra as Partial<InfraConfig>;
      config = deepMerge(config, envOverride);
    }
  } else {
    throw new Error(`Environment "${envName}" not found in environments.json`);
  }

  // Apply optional policy overlay if provided and exists
  if (opts?.policyOverlayPath && fs.existsSync(opts.policyOverlayPath)) {
    const policyContent = fs.readFileSync(opts.policyOverlayPath, 'utf-8');
    let policyData: { infra?: unknown };

    try {
      policyData = JSON.parse(policyContent);
    } catch (error) {
      throw new Error(`Failed to parse policy overlay: ${error}`);
    }

    if (policyData.infra && typeof policyData.infra === 'object' && policyData.infra !== null) {
      const policyOverride = policyData.infra as Partial<InfraConfig>;
      config = deepMerge(config, policyOverride);
    }
  }

  // Validate final merged config
  if (!isValidInfraConfig(config)) {
    throw new Error('Merged infra configuration is invalid');
  }

  // Check vendor-neutrality
  isVendorNeutral(config);

  // Freeze and return
  const frozenConfig = deepFreeze(config);

  return {
    config: frozenConfig,
    isEnabled: frozenConfig.feature_flags.infra_enabled,
  };
}
