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
                - name: sonar
                  image: sonarsource/sonar-scanner-cli:latest
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
        CLUSTER_NAME = "hadoop-dataproc"
        REGION = "us-central1"
        STAGING_BUCKET = "gs://mayavi-staging-bucket"
        // SCANNER_HOME = tool 'SonarScanner'
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
                container('sonar'){
                    withSonarQubeEnv(credentialsId: 'sonarqube-token', installationName: 'Sonarqube') {
                        // sh "${SCANNER_HOME}/bin/sonar-scanner"
                        sh 'sonar-scanner'
                    }
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
                container('gcloud') {
                    withCredentials([file(credentialsId: 'gcp-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                        script {
                            writeFile file: 'mapper.py', text: '''#!/usr/bin/env python3
import os
import sys

input_file = os.environ.get("map_input_file") or os.environ.get("mapreduce_map_input_file") or "unknown"
filename = os.path.basename(input_file)
line_count = 0
for _ in sys.stdin:
    line_count += 1

print('"{}"\t{}'.format(filename, line_count))
'''
                            writeFile file: 'reducer.py', text: '''#!/usr/bin/env python3
import sys

def safe_emit(name, count):
    if name is not None:
        print('{}: {}'.format(name, count))

def main():
    current_file = None
    total_lines = 0

    for raw in sys.stdin:
        try:
            line = raw.rstrip()
            if not line:
                continue
            parts = line.split(chr(9), 1)
            if len(parts) != 2:
                continue

            file_name, count_str = parts[0], parts[1].strip()
            count = int(count_str)

            if file_name == current_file:
                total_lines += count
            else:
                safe_emit(current_file, total_lines)
                current_file = file_name
                total_lines = count
        except Exception:
            continue

    safe_emit(current_file, total_lines)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass
'''
                        }

                        sh '''
                        gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                        gcloud config set project ${PROJECT_ID}

                        gsutil rm -r ${STAGING_BUCKET}/input/ || true
                        gsutil rm -r ${STAGING_BUCKET}/output/ || true
                        rm -rf mayavi || true
                        git clone https://github.com/Liyixian06/mayavi.git
                        cd mayavi
                        gsutil -m rsync -r -x '.*\\.(jpg|jpeg|png|gif|svg|bmp|pdf|zip|bin)$|\\.git.*' . ${STAGING_BUCKET}/input/
                        
                        cd ../
                        ls -l mapper.py reducer.py
                        cat mapper.py
                        sed -i 's/\r$//' mapper.py reducer.py
                        chmod +x mapper.py reducer.py
                        gsutil cp mapper.py reducer.py ${STAGING_BUCKET}/streaming/

                        gcloud dataproc jobs submit hadoop \
                        --cluster=${CLUSTER_NAME} \
                        --region=${REGION} \
                        --project=${PROJECT_ID} \
                        --class=org.apache.hadoop.streaming.HadoopStreaming \
                        --jars=file:///usr/lib/hadoop/hadoop-streaming.jar \
                        --files=${STAGING_BUCKET}/streaming/mapper.py,${STAGING_BUCKET}/streaming/reducer.py \
                        -- -D mapreduce.input.fileinputformat.input.dir.recursive=true \
                        -D mapreduce.job.reduces=1 \
                        -mapper "python3 mapper.py" \
                        -reducer "python3 reducer.py" \
                        -input ${STAGING_BUCKET}/input/* \
                        -output ${STAGING_BUCKET}/output/
                        
                        gsutil cat ${STAGING_BUCKET}/output/* > merged-output
                        cat merged-output
                        '''
                    }
                }
            }
        }
    }
}
