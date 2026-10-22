pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    triggers {
        githubPush()
    }

    environment {
        IMAGE   = 'two-tier-web'
        PROJECT = 'twotier'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    docker run --rm -v "$PWD/app":/app -w /app python:3.12-slim \
                      sh -c "pip install -q -r requirements.txt pytest && pytest -q"
                '''
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build -t $IMAGE:$BUILD_NUMBER -t $IMAGE:latest ./app'
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([string(credentialsId: 'db-password', variable: 'DB_PASSWORD')]) {
                    sh 'docker compose -p $PROJECT up -d --build'
                }
            }
        }

        stage('Health check') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                      if curl -fs http://localhost/health; then echo; exit 0; fi
                      sleep 3
                    done
                    echo "Health check failed"; exit 1
                '''
            }
        }
    }

    post {
        failure {
            sh 'docker compose -p $PROJECT logs --tail=50 || true'
        }
        always {
            sh 'docker image prune -f || true'
        }
    }
}
