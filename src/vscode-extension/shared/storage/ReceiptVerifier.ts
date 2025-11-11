import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { toCanonicalJson } from './CanonicalJson';
import { StoragePathResolver } from './StoragePathResolver';

const TRUST_STORE_RELATIVE_PATHS = [
    ['product', 'policy', 'trust', 'pubkeys'],
    ['tenant', 'policy', 'trust', 'pubkeys']
] as const;

const ED25519_PREFIX = 'sig-ed25519:';

export class PublicKeyNotFoundError extends Error {
    constructor(public readonly kid: string, public readonly searchedDirectories: string[]) {
        super(`Public key not found for kid "${kid}" in directories: ${searchedDirectories.join(', ')}`);
    }
}

export class UnsupportedPublicKeyFormatError extends Error {
    constructor(public readonly filePath: string) {
        super(`Unsupported public key format in file: ${filePath}`);
    }
}

type ReceiptRecord = Record<string, unknown>;

interface ParsedSignature {
    kid: string;
    signature: Buffer;
}

const isObject = (value: unknown): value is ReceiptRecord =>
    typeof value === 'object' && value !== null && !Array.isArray(value);

const parseSignature = (signatureValue: unknown): ParsedSignature | null => {
    if (typeof signatureValue !== 'string' || signatureValue.length === 0) {
        return null;
    }

    if (!signatureValue.startsWith(ED25519_PREFIX)) {
        return null;
    }

    const [, kid, base64] = signatureValue.split(':');
    if (!kid || !base64) {
        return null;
    }

    if (!/^[A-Za-z0-9._-]+$/.test(kid)) {
        return null;
    }

    try {
        const signature = Buffer.from(base64, 'base64');
        return { kid, signature };
    } catch {
        return null;
    }
};

const ensurePemPublicKey = (content: string, sourcePath: string): void => {
    if (!content.includes('-----BEGIN PUBLIC KEY-----') || !content.includes('-----END PUBLIC KEY-----')) {
        throw new UnsupportedPublicKeyFormatError(sourcePath);
    }
};

const stripSignatureField = (receipt: ReceiptRecord): ReceiptRecord => {
    const { signature: _ignored, ...rest } = receipt;
    return rest;
};

export const computeSignableReceiptBuffer = (receipt: object): Buffer => {
    if (!isObject(receipt)) {
        throw new TypeError('Receipt must be a plain object for canonicalisation');
    }

    const signable = stripSignatureField({ ...receipt });
    const canonicalJson = toCanonicalJson(signable);
    return Buffer.from(canonicalJson, 'utf-8');
};

export const verifyReceiptSignature = (
    receipt: object,
    publicKeyPemOrRaw: string | Buffer
): boolean => {
    if (!isObject(receipt)) {
        return false;
    }

    const parsed = parseSignature(receipt.signature);
    if (!parsed) {
        return false;
    }

    try {
        const publicKey = crypto.createPublicKey(publicKeyPemOrRaw);
        const signableBuffer = computeSignableReceiptBuffer(receipt);
        return crypto.verify(null, signableBuffer, publicKey, parsed.signature);
    } catch (error) {
        console.warn(`Receipt signature verification failed: ${(error as Error).message}`);
        return false;
    }
};

export const resolvePublicKeyByKid = (
    kid: string
): { key: string; sourcePath: string } => {
    if (!/^[A-Za-z0-9._-]+$/.test(kid)) {
        throw new Error(`Invalid key identifier: ${kid}`);
    }

    let zuRoot: string;
    try {
        const resolver = new StoragePathResolver();
        zuRoot = resolver.getZuRoot();
    } catch (error) {
        throw new Error(`Unable to resolve ZU_ROOT for trust store lookup: ${(error as Error).message}`);
    }

    const searchedDirectories: string[] = [];

    for (const relativeParts of TRUST_STORE_RELATIVE_PATHS) {
        const directory = path.join(zuRoot, ...relativeParts);
        searchedDirectories.push(directory);

        if (!fs.existsSync(directory)) {
            continue;
        }

        const entries = fs.readdirSync(directory).sort();
        for (const entry of entries) {
            const entryPath = path.join(directory, entry);

            if (!fs.statSync(entryPath).isFile()) {
                continue;
            }

            const baseName = path.parse(entry).name;
            if (baseName !== kid) {
                continue;
            }

            const content = fs.readFileSync(entryPath, 'utf-8');
            ensurePemPublicKey(content, entryPath);

            return {
                key: content,
                sourcePath: entryPath
            };
        }
    }

    throw new PublicKeyNotFoundError(kid, searchedDirectories);
};

export const extractKidFromSignature = (signatureValue: unknown): string | null => {
    const parsed = parseSignature(signatureValue);
    return parsed ? parsed.kid : null;
};

