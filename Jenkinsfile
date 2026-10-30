pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Test api') {
            steps {
                dir('services/api') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install -r requirements-dev.txt
                        pytest -v
                    '''
                }
            }
        }

        stage('Test inventory') {
            steps {
                dir('services/inventory') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install -r requirements-dev.txt
                        pytest -v
                    '''
                }
            }
        }

        stage('Build images') {
            steps {
                sh 'docker build -t flask-api:${BUILD_NUMBER} services/api'
                sh 'docker build -t flask-inventory:${BUILD_NUMBER} services/inventory'
            }
        }
    }
}