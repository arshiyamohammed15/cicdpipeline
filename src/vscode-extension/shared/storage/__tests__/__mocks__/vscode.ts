/**
 * Manual mock for vscode module
 * Used in tests where vscode is not available
 */

export const workspace = {
    getConfiguration: jest.fn().mockReturnValue({
        get: jest.fn().mockReturnValue(undefined)
    })
};

export const window = {
    showWarningMessage: jest.fn(),
    showErrorMessage: jest.fn()
};

