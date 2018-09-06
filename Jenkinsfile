#!/usr/bin/env groovy
pipeline {
  agent none // Allows stages to be built on different labels

  stages {
    stage('Tests') {
      environment {
        WORKSPACE = "${workspace}"
        AWS_DEFAULT_REGION = "us-east-1"
      }
      agent { label 'linux' }
      steps {
        withCredentials([usernamePassword(credentialsId: '8e64020a-fe1f-4fb5-865c-2fcfdacea39e', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh("$WORKSPACE/build/tests")
        } // End of Credentials
      } // steps
      post {
        always {
          junit "artifacts/*.xml"
        }
      }
    } // Test stage
  } // End of the Stages
} // End of the pipeline
