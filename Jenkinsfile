pipeline {
    agent {
        kubernetes {
            defaultContainer 'gcloud'
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              containers:
                - name: gcloud
                  image: google/cloud-sdk:slim
                  command: ['cat']
                  tty: true
            """
        }
    }
    triggers {
        githubPush()
    }
    environment {
        PROJECT_ID = "cmu-class-485820"
        CLUSTER_NAME = "devops-mayavi"
        REGION = "us-central1-b"
        STAGING_BUCKET = "gs://mayavi-staging-bucket"
        SCANNER_HOME = tool 'SonarScanner'
    }
    stages {
        stage('Print Info') {
            steps {
                echo "New code pushed to main branch!"
            }
        }
        // run sonarqube test
        stage('Run Sonarqube') {
            steps {
              withSonarQubeEnv(credentialsId: 'sonarqube-token', installationName: 'Sonarqube') {
                sh "${SCANNER_HOME}/bin/sonar-scanner"
              }
            }
        }

        stage("Quality Gate") {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to quality gate failure: ${qg.status}"
                        } else {
                            echo "SonarQube analysis passed (Status: ${qg.status}), continue to run Hadoop job"
                        }
                    }
                }
            }
        }

        stage('Run Hadoop Job') {
            steps {
                script {
                    sh '''
                    gsutil rm -r ${STAGING_BUCKET}/input/ || true
                    gsutil rm -r ${STAGING_BUCKET}/output/ || true
                    rm -rf mayavi || true
                    git clone https://github.com/Liyixian06/mayavi.git
                    cd mayavi
                    gsutil -m rsync -r -x '.*\\.(jpg|jpeg|png|gif|svg|bmp|pdf|zip|bin)$|\\.git.*' . ${STAGING_BUCKET}/input/
                    
                    cat << 'EOF' > mapper.sh
                    #!/bin/bash
                    FILENAME=\$(basename "\$map_input_file")
                    LINE_COUNT=\$(cat - | wc -l)
                    echo -e "\\"\$FILENAME\\"\\t\$LINE_COUNT"
                    EOF
                    
                    cat << 'EOF' > reducer.sh
                    #!/bin/bash
                    current_file=""
                    total_lines=0
                    while IFS=\$'\\t' read -r file count; do
                        if [ "\$file" == "\$current_file" ]; then
                            total_lines=\$((total_lines + count))
                        else
                            if [ -n "\$current_file" ]; then
                                echo "\$current_file: \$total_lines"
                            fi
                            current_file="\$file"
                            total_lines=\$count
                        fi
                    done
                    if [ -n "\$current_file" ]; then
                        echo "\$current_file: \$total_lines"
                    fi
                    EOF
                    chmod +x mapper.sh reducer.sh

                    gcloud dataproc jobs submit hadoop \
                      --cluster=${CLUSTER_NAME} \
                      --region=${REGION} \
                      --project=${PROJECT_ID} \
                      --class=org.apache.hadoop.streaming.HadoopStreaming \
                      --jars=file:///usr/lib/hadoop/hadoop-streaming.jar \
                      --files mapper.sh,reducer.sh \
                      -- -D mapreduce.input.fileinputformat.input.dir.recursive=true \
                      -D mapreduce.job.reduces=1 \
                      -mapper mapper.sh \
                      -reducer reducer.sh \
                      -input ${STAGING_BUCKET}/input/* \
                      -output ${STAGING_BUCKET}/output/
                    '''
                }
            }
        }
    }
}
