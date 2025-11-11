- **Trust store directories scanned**
  - `product/policy/trust/pubkeys/`
    - `pscl-dev.pem` → Ed25519 public key (`KID: pscl-dev`)
  - `tenant/policy/trust/pubkeys/`
    - `pscl-dev.pem` → Ed25519 public key (`KID: pscl-dev`)

- **Next steps**
  - Use the dev-only generator at `.zeroui/verify/gen_dev_keys.mjs` to create local Ed25519 test keys. The script writes:
    - Public keys to `.zeroui/verify/trust/pubkeys/{kid}.pem`
    - Private keys to `.zeroui/verify/trust/keys/{kid}.pem` (remains ignored by git)
  - Point local tests or harnesses at the generated trust store by exporting `ZU_ROOT` (or setting `zeroui.zuRoot` in VS Code) to the absolute path of `.zeroui/verify`.
  - Do **not** copy dev keys into `product/` or `tenant/` trust stores; only checked-in PEMs belong there.

- **Stop conditions**
  - If production or tenant trust-store PEMs are added in the future, update this document with their paths so verifiers can locate them.
## PSCL Key Discovery

- **Receipt signer module**: `src/vscode-extension/shared/storage/ReceiptSigner.ts`
- **Receipt verifier module**: `src/vscode-extension/shared/storage/ReceiptVerifier.ts`
- **Receipt reader module**: `src/vscode-extension/shared/storage/ReceiptStorageReader.ts`
- **Trust store directories examined**:
  - `product/policy/trust/pubkeys/`
  - `tenant/policy/trust/pubkeys/`
- **Existing KID→public key resolver**: `resolvePublicKeyByKid` in `src/vscode-extension/shared/storage/ReceiptVerifier.ts`
- **Observed public key formats**:
    - PEM (`-----BEGIN PUBLIC KEY-----`) committed for `pscl-dev` in both product and tenant planes
    - Additional keys can be supplied locally via `.zeroui/verify/trust/pubkeys/` when running the verification harness


