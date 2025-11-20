"use strict";
/**
 * LocalIngress
 *
 * Local file-based implementation of IngressPort.
 * Uses route table JSON and TLS config JSON persisted (no keys stored).
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
exports.LocalIngress = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const InfraConfig_1 = require("../../../../config/InfraConfig");
class LocalIngress {
    constructor(baseDir, envName = 'development') {
        this.routeTable = {};
        this.tlsConfig = {};
        this.globalTls = null;
        this.stats = new Map();
        this.baseDir = baseDir;
        this.envName = envName;
        this.routeTableFile = path.join(baseDir, 'route-table.json');
        this.tlsConfigFile = path.join(baseDir, 'tls-config.json');
        this.globalTlsFile = path.join(baseDir, 'global-tls.json');
        this.loadConfigs();
    }
    async createRule(rule) {
        const ruleId = rule.id || this.generateRuleId();
        const ruleWithId = { ...rule, id: ruleId };
        this.routeTable[ruleId] = ruleWithId;
        // Persist TLS config if present
        if (rule.tls) {
            this.tlsConfig[ruleId] = {
                enabled: rule.tls.enabled,
                certificateId: rule.tls.certificateId,
                minVersion: rule.tls.minVersion,
            };
        }
        await this.saveConfigs();
        // Initialize stats
        this.stats.set(ruleId, {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            activeConnections: 0,
            targetHealth: 'healthy',
        });
        return ruleId;
    }
    async deleteRule(ruleId) {
        delete this.routeTable[ruleId];
        delete this.tlsConfig[ruleId];
        this.stats.delete(ruleId);
        await this.saveConfigs();
    }
    async getRule(ruleId) {
        const rule = this.routeTable[ruleId];
        if (!rule) {
            throw new Error(`Ingress rule ${ruleId} not found`);
        }
        // Merge TLS config if present
        if (this.tlsConfig[ruleId]) {
            rule.tls = {
                enabled: this.tlsConfig[ruleId].enabled,
                certificateId: this.tlsConfig[ruleId].certificateId,
                minVersion: this.tlsConfig[ruleId].minVersion,
            };
        }
        return rule;
    }
    async listRules(options) {
        let rules = Object.values(this.routeTable);
        // Filter by host if specified
        if (options?.host) {
            rules = rules.filter((rule) => rule.host === options.host);
        }
        // Merge TLS configs
        rules = rules.map((rule) => {
            if (this.tlsConfig[rule.id]) {
                rule.tls = {
                    enabled: this.tlsConfig[rule.id].enabled,
                    certificateId: this.tlsConfig[rule.id].certificateId,
                    minVersion: this.tlsConfig[rule.id].minVersion,
                };
            }
            return rule;
        });
        // Limit results
        if (options?.maxResults) {
            rules = rules.slice(0, options.maxResults);
        }
        return rules;
    }
    async getStats(ruleId) {
        const stats = this.stats.get(ruleId);
        if (!stats) {
            throw new Error(`Stats not found for ingress rule ${ruleId}`);
        }
        return { ...stats };
    }
    /**
     * Record a request (for stats tracking).
     */
    recordRequest(ruleId, success, responseTime) {
        const stats = this.stats.get(ruleId);
        if (!stats) {
            return;
        }
        stats.totalRequests++;
        if (success) {
            stats.successfulRequests++;
        }
        else {
            stats.failedRequests++;
        }
        if (responseTime !== undefined) {
            // Simple moving average
            stats.averageResponseTime = stats.averageResponseTime
                ? (stats.averageResponseTime + responseTime) / 2
                : responseTime;
        }
    }
    /**
     * Set global TLS configuration.
     * Persists JSON with certificate and key references (no private keys stored).
     */
    async setTls(config) {
        this.globalTls = {
            enabled: config.enabled,
            cert_ref: config.cert_ref,
            key_ref: config.key_ref,
        };
        await this.saveGlobalTls();
    }
    /**
     * Get compliance status based on infra.network.tls_required and TLS enabled status.
     */
    status() {
        try {
            const infraResult = (0, InfraConfig_1.loadInfraConfig)(this.envName);
            const tlsRequired = infraResult.config.network.tls_required;
            // If TLS is required by infra config but not enabled, return NON_COMPLIANT
            if (tlsRequired && (!this.globalTls || !this.globalTls.enabled)) {
                return 'NON_COMPLIANT';
            }
            return 'COMPLIANT';
        }
        catch (error) {
            // If we can't load infra config, assume compliant (fail open)
            return 'COMPLIANT';
        }
    }
    loadConfigs() {
        // Load route table
        if (fs.existsSync(this.routeTableFile)) {
            try {
                const content = fs.readFileSync(this.routeTableFile, 'utf-8');
                this.routeTable = JSON.parse(content);
            }
            catch (error) {
                this.routeTable = {};
            }
        }
        // Load TLS config
        if (fs.existsSync(this.tlsConfigFile)) {
            try {
                const content = fs.readFileSync(this.tlsConfigFile, 'utf-8');
                this.tlsConfig = JSON.parse(content);
            }
            catch (error) {
                this.tlsConfig = {};
            }
        }
        // Load global TLS config
        if (fs.existsSync(this.globalTlsFile)) {
            try {
                const content = fs.readFileSync(this.globalTlsFile, 'utf-8');
                this.globalTls = JSON.parse(content);
            }
            catch (error) {
                this.globalTls = null;
            }
        }
        // Initialize stats for existing rules
        for (const ruleId of Object.keys(this.routeTable)) {
            if (!this.stats.has(ruleId)) {
                this.stats.set(ruleId, {
                    totalRequests: 0,
                    successfulRequests: 0,
                    failedRequests: 0,
                    activeConnections: 0,
                    targetHealth: 'healthy',
                });
            }
        }
    }
    async saveConfigs() {
        await this.ensureDirectory(this.baseDir);
        // Save route table (no keys stored)
        await fs.promises.writeFile(this.routeTableFile, JSON.stringify(this.routeTable, null, 2), 'utf-8');
        // Save TLS config (no keys stored, only config)
        await fs.promises.writeFile(this.tlsConfigFile, JSON.stringify(this.tlsConfig, null, 2), 'utf-8');
    }
    async saveGlobalTls() {
        await this.ensureDirectory(this.baseDir);
        // Save global TLS config (no private keys, only references)
        await fs.promises.writeFile(this.globalTlsFile, JSON.stringify(this.globalTls, null, 2), 'utf-8');
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    generateRuleId() {
        return `ingress-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
}
exports.LocalIngress = LocalIngress;
//# sourceMappingURL=LocalIngress.js.map