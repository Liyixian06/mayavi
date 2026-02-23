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
    }
}
