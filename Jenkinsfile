pipeline {
    agent none

    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        APP_NAME      = 'hotspot_sleman'
        VENV_DIR      = '.venv_ci'
        ARTIFACT      = "${APP_NAME}-${BUILD_NUMBER}.tar.gz"
        DEPLOY_ROOT   = '/var/www/hotspot_sleman' // ini folder utama di server
    }

    stages {

        stage('Checkout') {
            agent { label 'controller' } // sesuaikan dengan label controller lo
            steps {
                checkout scm
                // KIRIM SEMUA KECUALI sampah; tests IKUT, tapi nanti TIDAK dimasukin artifact
                stash name: 'source',
                      includes: '**',
                      excludes: '.git/**, .venv/**, venv/**, __pycache__/**, runtime/**'
            }
        }

        stage('Install & Test (STB)') {
            agent { label 'stb' }
            steps {
                unstash 'source'
                sh """
                    set -e

                    python3 -m venv ${VENV_DIR} || true
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        stage('Package (STB)') {
            agent { label 'stb' }
            steps {
                sh """
                    set -e
                    tar czf ${ARTIFACT} \\
                        app.py \\
                        requirements.txt \\
                        scripts \\
                        static \\
                        templates \\
                        data \\
                        COLOR_LEGEND.md \\
                        COLOR_SYSTEM_DOCUMENTATION.md \\
                        QUICK_COLOR_REFERENCE.txt \\
                        TROUBLESHOOTING_PING.md || true
                """
                stash name: 'artifact', includes: "${ARTIFACT}"
                archiveArtifacts artifacts: "${ARTIFACT}", fingerprint: true
            }
        }

        stage('Deploy (PROD)') {
            // when { branch 'main' }
            agent { label 'prod' }
            steps {
                unstash 'artifact'
                sh """
                    set -e

                    SERVICE=hotspot_sleman

                    DEPLOY_ROOT=${DEPLOY_ROOT}
                    RELEASES_DIR=${DEPLOY_ROOT}/releases
                    CURRENT_LINK=${DEPLOY_ROOT}/current
                    DATA_DIR=${DEPLOY_ROOT}/data
                    RUNTIME_DIR=${DEPLOY_ROOT}/runtime

                    mkdir -p "$RELEASES_DIR" "$DATA_DIR" "$RUNTIME_DIR"

                    RELEASE_DIR="${RELEASES_DIR}/${APP_NAME}-${BUILD_NUMBER}"

                    sudo systemctl stop $SERVICE || true

                    rm -rf "$RELEASE_DIR"
                    mkdir -p "$RELEASE_DIR"
                    tar xzf "${ARTIFACT}" -C "$RELEASE_DIR"

                    # ACTIVATE VENV INSIDE RELEASE
                    python3 -m venv "$RELEASE_DIR/.venv"
                    . "$RELEASE_DIR/.venv/bin/activate"
                    pip install --upgrade pip
                    pip install -r "$RELEASE_DIR/requirements.txt"

                    # LINK TO CURRENT VERSION
                    ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"

                    sudo systemctl restart $SERVICE

                    sleep 5
                    curl -f http://localhost:8000/ || (echo "Healthcheck failed" && exit 1)
                """
            }
        }

    }
}
