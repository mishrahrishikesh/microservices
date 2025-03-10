pipeline{
    agent any
    parameters{
        choice(name: 'ACTION', choices:['deploy', 'destroy'], description: 'Choose to deploy or destroy the app')
    }
    stages{
        stage('Build') {
            steps{
                script{
                    if (params.ACTION == 'deploy'){
                        sh 'docker compose up -d'
                    }
                    else if (params.ACTION == 'destroy'){
                        sh 'docker compose down'
                    }
                    else{
                        echo 'Invalid Selection'
                    }
                }
            }
        }
    }
}
