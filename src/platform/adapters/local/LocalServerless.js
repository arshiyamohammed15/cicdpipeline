"use strict";
/**
 * LocalServerless
 *
 * Local file-based implementation of ServerlessPort using JS function registry.
 * Functions are stored in a known folder and invoked with timeout.
 * Execution logs are appended to NDJSON.
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
exports.LocalServerless = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalServerless {
    constructor(functionsDir, logsFile, defaultTimeout = 30000) {
        this.registry = {};
        this.functionsDir = functionsDir;
        this.logsFile = logsFile;
        this.defaultTimeout = defaultTimeout;
        this.loadRegistry();
    }
    async invoke(functionName, payload, options) {
        const requestId = this.generateRequestId();
        const startTime = this.getMonotonicTime();
        const timeout = options?.timeout || this.defaultTimeout;
        if (!this.registry[functionName]) {
            const error = `Function ${functionName} not found`;
            await this.logExecution({
                functionName,
                requestId,
                status: 'error',
                error,
                duration: this.getMonotonicTime() - startTime,
                timestamp: startTime,
            });
            return {
                status: 'error',
                error,
                duration: this.getMonotonicTime() - startTime,
                requestId,
            };
        }
        try {
            const functionInfo = this.registry[functionName];
            const functionCode = fs.readFileSync(functionInfo.filePath, 'utf-8');
            // Create isolated execution context
            const result = await this.executeWithTimeout(functionCode, payload, timeout, options?.environment);
            const duration = this.getMonotonicTime() - startTime;
            const memoryUsed = this.estimateMemoryUsage(result);
            await this.logExecution({
                functionName,
                requestId,
                status: 'success',
                payload: typeof result === 'string' ? result : JSON.stringify(result),
                duration,
                memoryUsed,
                timestamp: startTime,
            });
            return {
                status: 'success',
                payload: result,
                duration,
                memoryUsed,
                requestId,
            };
        }
        catch (error) {
            const duration = this.getMonotonicTime() - startTime;
            const errorMessage = error instanceof Error ? error.message : String(error);
            await this.logExecution({
                functionName,
                requestId,
                status: errorMessage.includes('timeout') ? 'timeout' : 'error',
                error: errorMessage,
                duration,
                timestamp: startTime,
            });
            return {
                status: errorMessage.includes('timeout') ? 'timeout' : 'error',
                error: errorMessage,
                duration,
                requestId,
            };
        }
    }
    async invokeAsync(functionName, payload, options) {
        const requestId = this.generateRequestId();
        // Fire and forget - invoke in background
        this.invoke(functionName, payload, options).catch(() => {
            // Errors logged in invoke()
        });
        return requestId;
    }
    async getFunctionConfig(functionName) {
        if (!this.registry[functionName]) {
            throw new Error(`Function ${functionName} not found`);
        }
        return this.registry[functionName].config;
    }
    loadRegistry() {
        if (!fs.existsSync(this.functionsDir)) {
            return;
        }
        const files = fs.readdirSync(this.functionsDir);
        for (const file of files) {
            if (file.endsWith('.js')) {
                const functionName = path.basename(file, '.js');
                const filePath = path.join(this.functionsDir, file);
                const configPath = path.join(this.functionsDir, `${functionName}.config.json`);
                let config = {
                    name: functionName,
                    status: 'active',
                };
                if (fs.existsSync(configPath)) {
                    try {
                        const configContent = fs.readFileSync(configPath, 'utf-8');
                        config = { ...config, ...JSON.parse(configContent) };
                    }
                    catch (error) {
                        // Use default config
                    }
                }
                this.registry[functionName] = {
                    filePath,
                    config,
                };
            }
        }
    }
    async executeWithTimeout(functionCode, payload, timeout, environment) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                reject(new Error('Function execution timeout'));
            }, timeout);
            try {
                // Create isolated context with environment variables
                const context = {
                    ...(environment || {}),
                    payload,
                    console: {
                        log: (...args) => {
                            // Suppress console output in production
                        },
                    },
                };
                // Execute function in isolated context
                // Note: This is a simplified execution - in production, use vm module or worker threads
                // Wrap function code to handle both arrow functions and regular functions
                const wrappedCode = functionCode.trim().startsWith('(')
                    ? `(${functionCode})`
                    : functionCode;
                const func = new Function('payload', `return (${wrappedCode})(payload);`);
                const result = func(payload);
                if (result instanceof Promise) {
                    result
                        .then((value) => {
                        clearTimeout(timer);
                        resolve(value);
                    })
                        .catch((error) => {
                        clearTimeout(timer);
                        reject(error);
                    });
                }
                else {
                    clearTimeout(timer);
                    resolve(result);
                }
            }
            catch (error) {
                clearTimeout(timer);
                reject(error);
            }
        });
    }
    estimateMemoryUsage(result) {
        // Rough estimation: JSON stringify size
        const size = JSON.stringify(result).length;
        return Math.ceil(size / 1024); // KB
    }
    async logExecution(log) {
        await this.ensureDirectory(path.dirname(this.logsFile));
        await this.appendToJsonl(this.logsFile, JSON.stringify(log));
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    async appendToJsonl(filePath, jsonContent) {
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
            await handle.sync();
        }
        finally {
            await handle.close();
        }
    }
    generateRequestId() {
        return `req-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    }
    getMonotonicTime() {
        return Date.now();
    }
}
exports.LocalServerless = LocalServerless;
//# sourceMappingURL=LocalServerless.js.map