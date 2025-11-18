/**
 * Jest Configuration for Storage Integration Tests
 */

module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'node',
    globals: {
        'ts-jest': {
            tsconfig: 'tsconfig.jest.json'
        }
    },
    roots: ['<rootDir>/src', '<rootDir>/tests'],
    testMatch: [
        '**/__tests__/**/*.test.ts',
        '**/?(*.)+(spec|test).ts'
    ],
    transform: {
        '^.+\\.ts$': 'ts-jest'
    },
    collectCoverageFrom: [
        'src/edge-agent/shared/storage/**/*.ts',
        'src/vscode-extension/shared/storage/**/*.ts',
        '!src/**/*.d.ts',
        '!src/**/__tests__/**'
    ],
    modulePathIgnorePatterns: [
        '<rootDir>/src/vscode-extension/out',
        '<rootDir>/src/vscode-extension/test'
    ],
    testPathIgnorePatterns: [
        '/node_modules/',
        '<rootDir>/src/vscode-extension/test/'
    ],
    coverageDirectory: 'coverage',
    coverageReporters: ['text', 'lcov', 'html'],
    moduleFileExtensions: ['ts', 'js', 'json'],
    verbose: true,
    clearMocks: true,
    resetMocks: true,
    restoreMocks: true
};
