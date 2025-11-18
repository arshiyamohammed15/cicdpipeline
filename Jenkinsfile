pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        NODE_VERSION = '20'
        ZU_ROOT = "${WORKSPACE}/storage"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                script {
                    // Setup Python environment
                    sh '''
                        python${PYTHON_VERSION} -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''

                    // Setup Node.js environment
                    sh '''
                        cd src/vscode-extension
                        npm ci
                        cd ../edge-agent
                        npm ci
                    '''
                }
            }
        }

        stage('Lint') {
            parallel {
                stage('Python Lint') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            pylint src/cloud-services/ || true
                            flake8 src/cloud-services/ || true
                            mypy src/cloud-services/ || true
                        '''
                    }
                }
                stage('TypeScript Lint') {
                    steps {
                        sh '''
                            cd src/vscode-extension
                            npm run lint
                            cd ../edge-agent
                            npm run lint
                        '''
                    }
                }
                stage('Markdown Lint') {
                    steps {
                        sh '''
                            markdownlint docs/**/*.md || true
                        '''
                    }
                }
            }
        }

        stage('Format Check') {
            steps {
                sh '''
                    . venv/bin/activate
                    black --check src/cloud-services/ || true
                    cd src/vscode-extension
                    npm run format:check
                '''
            }
        }

        stage('Tests') {
            parallel {
                stage('Python Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            pytest --cov=src/cloud-services --cov-report=html --cov-report=xml -v
                        '''
                    }
                    post {
                        always {
                            publishHTML([
                                reportDir: 'htmlcov',
                                reportFiles: 'index.html',
                                reportName: 'Python Coverage Report'
                            ])
                            publishCoverage adapters: [
                                coberturaAdapter('coverage.xml')
                            ]
                        }
                    }
                }
                stage('TypeScript Tests') {
                    steps {
                        sh '''
                            cd src/vscode-extension
                            npm test -- --coverage
                            cd ../edge-agent
                            npm test -- --coverage
                        '''
                    }
                    post {
                        always {
                            publishCoverage adapters: [
                                jestAdapter('src/vscode-extension/coverage/coverage-final.json'),
                                jestAdapter('src/edge-agent/coverage/coverage-final.json')
                            ]
                        }
                    }
                }
            }
        }

        stage('Architecture Validation') {
            steps {
                sh '''
                    . venv/bin/activate
                    python scripts/ci/verify_architecture_artifacts.py
                    python scripts/ci/check_hardcoded_rules.py
                    python scripts/ci/check_privacy_split.py
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    cd src/vscode-extension
                    npm run build
                    cd ../edge-agent
                    npm run build
                '''
            }
        }

        stage('Export Diagrams') {
            steps {
                sh '''
                    # Export architecture diagrams if tools available
                    if command -v mmdc &> /dev/null; then
                        mmdc -i docs/architecture/*.mmd -o docs/architecture/exports/ || true
                    fi
                    if command -v plantuml &> /dev/null; then
                        plantuml docs/architecture/*.puml -o docs/architecture/exports/ || true
                    fi
                '''
            }
        }

        stage('Package Artifacts') {
            steps {
                sh '''
                    mkdir -p artifacts
                    # Package VS Code Extension
                    cd src/vscode-extension
                    npm run package
                    cp *.vsix ../../artifacts/ || true
                    # Package Edge Agent
                    cd ../edge-agent
                    npm run package
                    cp *.tar.gz ../../artifacts/ || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'artifacts/**/*', fingerprint: true
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    . venv/bin/activate
                    # Python security scan
                    pip install safety
                    safety check || true
                    # Node.js security scan
                    cd src/vscode-extension
                    npm audit --audit-level=moderate || true
                    cd ../edge-agent
                    npm audit --audit-level=moderate || true
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            emailext(
                subject: "Build Success: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build succeeded. See ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
        failure {
            emailext(
                subject: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build failed. See ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
