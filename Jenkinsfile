pipeline {
    agent any
    triggers {
        githubPush()
    }
    stages {
        stage('Print Info') {
            steps {
                echo "New code pushed to main branch!"
            }
        }
        // run sonarqube test
        stage('Run Sonarqube') {
            environment {
                scannerHome = tool 'SonarScanner';
            }
            steps {
              withSonarQubeEnv(credentialsId: 'sonarqube', installationName: 'Sonarqube') {
                sh "${scannerHome}/bin/sonar-scanner"
              }
            }
        }
    }
}
