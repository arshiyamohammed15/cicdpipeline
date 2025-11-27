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
                        pip install ".[dev]"
                        pip install -r requirements-api.txt
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
                            mkdir -p artifacts/evidence
                            pytest --cov=src/cloud-services --cov-report=html --cov-report=xml \
                                --junit-xml=artifacts/junit.xml \
                                -v \
                                -p tests.pytest_evidence_plugin
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
                            // Archive evidence packs
                            archiveArtifacts artifacts: 'artifacts/evidence/*.zip', allowEmptyArchive: true
                            // Archive JUnit XML for test reporting
                            junit 'artifacts/junit.xml'
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

        stage('Mandatory Test Suites') {
            steps {
                sh '''
                    . venv/bin/activate
                    mkdir -p artifacts/evidence
                    # Run mandatory test suites (fail build if any fail)
                    echo "Running mandatory DG&P regression tests..."
                    pytest -m "dgp_regression" --junit-xml=artifacts/junit-dgp-regression.xml -v -p tests.pytest_evidence_plugin || exit 1
                    
                    echo "Running mandatory DG&P security tests..."
                    pytest -m "dgp_security" --junit-xml=artifacts/junit-dgp-security.xml -v -p tests.pytest_evidence_plugin || exit 1
                    
                    echo "Running mandatory DG&P performance tests..."
                    pytest -m "dgp_performance" --junit-xml=artifacts/junit-dgp-performance.xml -v -p tests.pytest_evidence_plugin || exit 1
                    
                    # Alerting mandatory suites (if tests exist)
                    if pytest -m "alerting_regression" --collect-only -q 2>/dev/null | grep -q "test session starts"; then
                        echo "Running mandatory Alerting regression tests..."
                        pytest -m "alerting_regression" --junit-xml=artifacts/junit-alerting-regression.xml -v -p tests.pytest_evidence_plugin || exit 1
                    fi
                    
                    if pytest -m "alerting_security" --collect-only -q 2>/dev/null | grep -q "test session starts"; then
                        echo "Running mandatory Alerting security tests..."
                        pytest -m "alerting_security" --junit-xml=artifacts/junit-alerting-security.xml -v -p tests.pytest_evidence_plugin || exit 1
                    fi
                    
                    # Budgeting mandatory suites (if tests exist)
                    if pytest -m "budgeting_regression" --collect-only -q 2>/dev/null | grep -q "test session starts"; then
                        echo "Running mandatory Budgeting regression tests..."
                        pytest -m "budgeting_regression" --junit-xml=artifacts/junit-budgeting-regression.xml -v -p tests.pytest_evidence_plugin || exit 1
                    fi
                    
                    # Deployment mandatory suites (if tests exist)
                    if pytest -m "deployment_regression" --collect-only -q 2>/dev/null | grep -q "test session starts"; then
                        echo "Running mandatory Deployment regression tests..."
                        pytest -m "deployment_regression" --junit-xml=artifacts/junit-deployment-regression.xml -v -p tests.pytest_evidence_plugin || exit 1
                    fi
                '''
            }
            post {
                always {
                    // Archive all evidence packs
                    archiveArtifacts artifacts: 'artifacts/evidence/*.zip', allowEmptyArchive: true
                    // Archive JUnit reports
                    junit 'artifacts/junit-*.xml'
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
                    python scripts/ci/check_storage_resolver_contract.py
                    python scripts/ci/verify_constitution_consistency.py
                    # Backend convergence check
                    python -c "from config.constitution.sync_manager import verify_sync; result = verify_sync(); assert result.get('synchronized', False), f'Backend sync failed: {result}'; print('Backend sync verified')"
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
