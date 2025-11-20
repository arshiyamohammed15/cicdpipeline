"use strict";
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
exports.loadInfraConfig = exports.isVendorNeutral = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
// Vendor identifiers to detect
const VENDOR_IDENTIFIERS = ['aws', 's3', 'azure', 'gcs', 'kms', 'arn'];
/**
 * Deep freeze an object recursively
 */
function deepFreeze(obj) {
    Object.freeze(obj);
    if (obj === null || obj === undefined) {
        return obj;
    }
    Object.getOwnPropertyNames(obj).forEach((prop) => {
        if (obj[prop] !== null &&
            typeof obj[prop] === 'object' &&
            !Object.isFrozen(obj[prop])) {
            deepFreeze(obj[prop]);
        }
    });
    return obj;
}
/**
 * Type guard: Check if value is a valid integer >= 0
 */
function isNonNegativeInteger(value) {
    return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}
/**
 * Type guard: Check if value is a boolean
 */
function isBoolean(value) {
    return typeof value === 'boolean';
}
/**
 * Type guard: Check if value is a string
 */
function isString(value) {
    return typeof value === 'string';
}
/**
 * Type guard: Check if value is a valid routing default
 */
function isRoutingDefault(value) {
    return value === 'serverless' || value === 'gpu-queue' || value === 'batch';
}
/**
 * Type guard: Check if value is a valid cost profile
 */
function isCostProfile(value) {
    return value === 'light' || value === 'ai-inference' || value === 'batch';
}
/**
 * Type guard: Check if value is an array of cost profiles
 */
function isCostProfilesArray(value) {
    if (!Array.isArray(value)) {
        return false;
    }
    return value.every(isCostProfile);
}
/**
 * Type guard: Validate InfraCompute
 */
function isValidCompute(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isNonNegativeInteger(obj.min_baseline) &&
        isBoolean(obj.allow_spot) &&
        Object.keys(obj).length === 2);
}
/**
 * Type guard: Validate InfraRouting
 */
function isValidRouting(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isRoutingDefault(obj.default) &&
        isCostProfilesArray(obj.cost_profiles) &&
        Object.keys(obj).length === 2);
}
/**
 * Type guard: Validate InfraStorage
 */
function isValidStorage(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isString(obj.object_root) &&
        isString(obj.backups_root) &&
        isBoolean(obj.encryption_at_rest) &&
        Object.keys(obj).length === 3);
}
/**
 * Type guard: Validate InfraNetwork
 */
function isValidNetwork(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return isBoolean(obj.tls_required) && Object.keys(obj).length === 1;
}
/**
 * Type guard: Validate InfraObservability
 */
function isValidObservability(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isBoolean(obj.enable_metrics) &&
        isBoolean(obj.enable_cost) &&
        Object.keys(obj).length === 2);
}
/**
 * Type guard: Validate InfraDR
 */
function isValidDR(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isBoolean(obj.cross_zone) &&
        isNonNegativeInteger(obj.backup_interval_min) &&
        Object.keys(obj).length === 2);
}
/**
 * Type guard: Validate InfraFeatureFlags
 */
function isValidFeatureFlags(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isBoolean(obj.infra_enabled) &&
        isBoolean(obj.local_adapters_enabled) &&
        Object.keys(obj).length === 2);
}
/**
 * Type guard: Validate complete InfraConfig
 */
function isValidInfraConfig(value) {
    if (typeof value !== 'object' || value === null) {
        return false;
    }
    const obj = value;
    return (isValidCompute(obj.compute) &&
        isValidRouting(obj.routing) &&
        isValidStorage(obj.storage) &&
        isValidNetwork(obj.network) &&
        isValidObservability(obj.observability) &&
        isValidDR(obj.dr) &&
        isValidFeatureFlags(obj.feature_flags) &&
        Object.keys(obj).length === 7);
}
/**
 * Deep merge two objects, with source overriding target
 */
function deepMerge(target, source) {
    const result = {
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
function scanForVendorIdentifiers(obj, pathPrefix = '') {
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
            const result = scanForVendorIdentifiers(obj[key], currentPath);
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
function isVendorNeutral(infra) {
    const neutralFields = [
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
            throw new Error(`Vendor identifier detected in neutral infra field: ${offendingPath}`);
        }
    }
}
exports.isVendorNeutral = isVendorNeutral;
/**
 * Load and merge infrastructure configuration with precedence:
 * defaults (top-level infra) → per-env "infra" override → optional policy overlay
 */
function loadInfraConfig(envName, opts) {
    // Resolve paths relative to this file's directory
    // In CommonJS, __dirname is available; in ES modules, use import.meta.url
    // For compatibility, resolve from process.cwd() assuming config/ is at repo root
    const repoRoot = process.cwd();
    const environmentsPath = path.join(repoRoot, 'storage-scripts', 'config', 'environments.json');
    const schemaPath = path.join(repoRoot, 'config', 'infra.config.schema.json');
    // Verify schema file exists (reference documentation only, not used for validation)
    if (!fs.existsSync(schemaPath)) {
        throw new Error(`infra.config.schema.json not found at: ${schemaPath}`);
    }
    // Verify schema is valid JSON (but don't use it for validation - type-guards only)
    try {
        const schemaContent = fs.readFileSync(schemaPath, 'utf-8');
        JSON.parse(schemaContent);
    }
    catch (error) {
        throw new Error(`infra.config.schema.json is invalid JSON: ${error}`);
    }
    // Read environments.json
    if (!fs.existsSync(environmentsPath)) {
        throw new Error(`environments.json not found at: ${environmentsPath}`);
    }
    const environmentsContent = fs.readFileSync(environmentsPath, 'utf-8');
    let environmentsData;
    try {
        environmentsData = JSON.parse(environmentsContent);
    }
    catch (error) {
        throw new Error(`Failed to parse environments.json: ${error}`);
    }
    // Extract defaults (top-level infra)
    if (!environmentsData.infra) {
        throw new Error('Top-level "infra" block not found in environments.json');
    }
    if (!isValidInfraConfig(environmentsData.infra)) {
        throw new Error('Top-level "infra" block is invalid');
    }
    let config = { ...environmentsData.infra };
    // Apply per-environment override
    if (environmentsData.environments && environmentsData.environments[envName]) {
        const envData = environmentsData.environments[envName];
        if (envData.infra && typeof envData.infra === 'object' && envData.infra !== null) {
            const envOverride = envData.infra;
            config = deepMerge(config, envOverride);
        }
    }
    else {
        throw new Error(`Environment "${envName}" not found in environments.json`);
    }
    // Apply optional policy overlay if provided and exists
    if (opts?.policyOverlayPath && fs.existsSync(opts.policyOverlayPath)) {
        const policyContent = fs.readFileSync(opts.policyOverlayPath, 'utf-8');
        let policyData;
        try {
            policyData = JSON.parse(policyContent);
        }
        catch (error) {
            throw new Error(`Failed to parse policy overlay: ${error}`);
        }
        if (policyData.infra && typeof policyData.infra === 'object' && policyData.infra !== null) {
            const policyOverride = policyData.infra;
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
exports.loadInfraConfig = loadInfraConfig;
//# sourceMappingURL=InfraConfig.js.map