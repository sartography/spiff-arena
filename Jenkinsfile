pipeline {
  agent { label 'linux' }

  options {
    timestamps()
    timeout(time: 20, unit: 'MINUTES')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(
      numToKeepStr: '10',
      daysToKeepStr: '30',
    ))
  }

  parameters {
    string(
      name: 'COMPONENT',
      description: 'Name of component to build.',
      defaultValue: params.COMPONENT ?: 'backend'
    )
    string(
      name: 'DOCKER_TAG',
      description: 'Name of Docker tag to push. Chose wisely.',
      defaultValue: params.DOCKER_TAG ?: 'latest',
    )
    string(
      name: 'DOCKER_NAME',
      description: 'Name of Docker image to push.',
      defaultValue: params.DOCKER_NAME ?: 'ghcr.io/sartography/spiffworkflow-backend',
    )
    string(
      name: 'DOCKER_CRED_ID',
      description: 'ID of Jenkins credential for Docker registry.',
      defaultValue: params.DOCKER_CRED_ID ?: 'MISSING'
    )
    booleanParam(
      name: 'PUBLISH',
      description: 'Publish built Docker images.',
      defaultValue: params.PUBLISH ?: false
    )
  }

  stages {
    stage('Build') {
      steps { script {
        dir("spiffworkflow-${params.COMPONENT}") {
          image = docker.build(
            "${params.DOCKER_NAME}:${env.GIT_COMMIT.take(8)}",
            "--label=commit='${env.GIT_COMMIT.take(8)}' ."
          )
        }
      } }
    }

    stage('Push') {
      when { expression {
        params.PUBLISH && params.DOCKER_CRED_ID != ''
      } }
      steps { script {
        withDockerRegistry([credentialsId: params.DOCKER_CRED_ID, url: ""]) {
          image.push()
          image.push(env.DOCKER_TAG)
        }
      } }
    }
  } // stages
  post {
    always  { sh 'docker image prune -f' }
    cleanup { cleanWs() }
  } // post
} // pipeline
