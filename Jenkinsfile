import groovy.json.JsonBuilder

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
    string(
      name: 'DISCORD_WEBHOOK_CRED',
      description: 'Name of cretential with Discord webhook',
      defaultValue: params.DISCORD_WEBHOOK_CRED ?: "",
    )
    booleanParam(
      name: 'PUBLISH',
      description: 'Publish built Docker images.',
      defaultValue: params.PUBLISH ?: false
    )
  }

  stages {
    stage('Prep') {
      steps { script {
        dir("spiffworkflow-${params.COMPONENT}") {
          def jobMetaJson = new JsonBuilder([
            git_commit: env.GIT_COMMIT.take(7),
            git_branch: env.GIT_BRANCH,
            build_id:   env.BUILD_ID,
          ]).toPrettyString()
          sh "echo '${jobMetaJson}' > version_info.json"
        }
      } }
    }

    stage('Build') {
      steps { script {
        dir("spiffworkflow-${params.COMPONENT}") {
          /* Tag and Commit is combined to avoid clashes of parallel builds. */
          image = docker.build(
            "${params.DOCKER_NAME}:${params.DOCKER_TAG}-${env.GIT_COMMIT.take(8)}",
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
    always  {
      script {
        sh 'docker image prune -f'
        if (params.DISCORD_WEBHOOK_CRED) {
          def result  = currentBuild.result.toLowerCase() ?: 'unknown'
          discordNotify(
            header: "SpiffWorkflow Docker image build ${result}!",
            cred: params.DISCORD_WEBHOOK_CRED,
          )
        } // if
      } // script
    } // always
    cleanup { cleanWs() }
  } // post
} // pipeline

def discordNotify(Map args=[:]) {
  def opts = [
    header: args.header ?: 'Deployment successful!',
    title:  args.title  ?: "${env.JOB_NAME}#${env.BUILD_NUMBER}",
    cred:   args.cred   ?: null,
  ]
  def repo = [
    url: GIT_URL.minus('.git'),
    branch: GIT_BRANCH.minus('origin/'),
    commit: GIT_COMMIT.take(8),
    prev: (
      env.GIT_PREVIOUS_SUCCESSFUL_COMMIT ?: env.GIT_PREVIOUS_COMMIT ?: 'master'
    ).take(8),
  ]
  wrap([$class: 'BuildUser']) {
    BUILD_USER_ID = env.BUILD_USER_ID
  }
  withCredentials([
    string(
      credentialsId: opts.cred,
      variable: 'DISCORD_WEBHOOK',
    ),
  ]) {
    discordSend(
      link: env.BUILD_URL,
      result: currentBuild.currentResult,
      webhookURL: env.DISCORD_WEBHOOK,
      title: opts.title,
      description: """
        ${opts.header}
        Image: [`${params.DOCKER_NAME}:${params.DOCKER_TAG}`](https://hub.docker.com/r/${params.DOCKER_NAME}/tags?name=${params.DOCKER_TAG})
        Branch: [`${repo.branch}`](${repo.url}/commits/${repo.branch})
        Commit: [`${repo.commit}`](${repo.url}/commit/${repo.commit})
        Diff: [`${repo.prev}...${repo.commit}`](${repo.url}/compare/${repo.prev}...${repo.commit})
        By: [`${BUILD_USER_ID}`](${repo.url}/commits?author=${BUILD_USER_ID})
      """,
    )
  }
}
