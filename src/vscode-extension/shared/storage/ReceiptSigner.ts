import * as crypto from 'crypto';
import { computeSignableReceiptBuffer } from './ReceiptVerifier';

export interface ReceiptSigner {
    signReceipt(receipt: Record<string, unknown>): string;
}

export interface Ed25519ReceiptSignerOptions {
    privateKey: string | Buffer;
    keyId: string;
}

export class Ed25519ReceiptSigner implements ReceiptSigner {
    private readonly privateKey: crypto.KeyObject;
    private readonly keyId: string;

    constructor(options: Ed25519ReceiptSignerOptions) {
        this.privateKey = crypto.createPrivateKey(options.privateKey);
        this.keyId = options.keyId;
    }

    public signReceipt(receipt: Record<string, unknown>): string {
        const signableBuffer = computeSignableReceiptBuffer(receipt);
        const signature = crypto.sign(null, signableBuffer, this.privateKey);
        return `sig-ed25519:${this.keyId}:${signature.toString('base64')}`;
    }
}
