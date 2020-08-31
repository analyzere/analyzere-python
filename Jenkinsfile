#!/usr/bin/env groovy
pipeline {
  agent none

  stages {
    stage('Tests') {
      environment {
        WORKSPACE = "${workspace}"
        AWS_DEFAULT_REGION = "us-east-2"
      }
      agent { label 'linux' }
      steps {
        withAWS(){
          script{
              def login = ecrLogin()
              sh("echo ${login}")
              sh("${login}")
              sh("$WORKSPACE/build/tests")
          }
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
