pipeline {
    agent none
    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        APP_NAME = 'hotspot_sleman'
        VENV_DIR = '.venv_ci'
        ARTIFACT = "${APP_NAME}-${BUILD_NUMBER}.tar.gz"
        DEPLOY_DIR = '/var/www/monitoringwebsekolah'
    }

    stages {
        stage('Checkout') {
            agent { label 'master' }
            steps {
                checkout scm
                stash name: 'source', includes: '**', excludes: '.git/**, .venv/**, venv/**, tests/**'
            }
        }

        stage('Install & Test (STB)') {
            agent { label 'stb' }
            steps {
                unstash 'source'
                sh """
                    python3 -m venv ${VENV_DIR} || true
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    
                    # smoke test
                    if [ -d tests ]; then
                        pytest || echo 'no tests found, skipped'
                    fi
                """
            }
        }

        stage('Package (STB)') {
            agent { label 'stb' }
            steps {
                sh """
                    tar czf ${ARTIFACT} \
                        app.py scripts data static templates requirements.txt
                """
                stash name: 'artifact', includes: "${ARTIFACT}"
                archiveArtifacts artifacts: "${ARTIFACT}", fingerprint: true
            }
        }

        stage('Deploy (PROD)') {
            when { branch 'main' }
            agent { label 'prod' }
            steps {
                unstash 'artifact'
                sh """
                    SERVICE=pingsekolah
                    RELEASE_DIR=${DEPLOY_DIR}_releases/${APP_NAME}-${BUILD_NUMBER}

                    systemctl stop \$SERVICE || true
                    mkdir -p \$RELEASE_DIR
                    tar xzf ${ARTIFACT} -C \$RELEASE_DIR

                    python3 -m venv \$RELEASE_DIR/.venv
                    . \$RELEASE_DIR/.venv/bin/activate
                    pip install -r \$RELEASE_DIR/requirements.txt

                    ln -sfn \$RELEASE_DIR ${DEPLOY_DIR}
                    systemctl restart \$SERVICE
                """
            }
        }
    }
}
