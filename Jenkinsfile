pipeline{
    agent any
    parameters{
        choice(name: 'ACTION', choices:['DEPLOY', 'DESTROY'], description: 'Choose to deploy or destroy the app')
    }
    stages{
        stage('Build') {
            steps{
                script{
                    if (params.ACTION == 'DEPLOY'){
                        sh 'docker compose up -d'
                    }
                    else{
                        sh 'docker compose down'
                    }
                }
            }
        }
    }
}
