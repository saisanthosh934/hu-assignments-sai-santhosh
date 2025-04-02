pipeline {
    agent any
    environment {
        APP_NAME = 'santhosh-sample-app'
        SONAR_SERVER = 'sonar-server'
        DOCKER_CREDENTIALS_ID = 'docker-credentials-id'
        DEPLOYMENT_FILE = 'kubernetes-manifest/deployment.yaml'
        DOCKER_USERNAME = 'saisanthosh934'
    }
    stages {
        stage("Checkout") {
            steps {
                git branch: 'main', url: 'https://github.com/saisanthosh934/santhosh-python-app'
            }
        }


        stage('SonarQube Analysis') {
            steps {

                withCredentials([usernamePassword(credentialsId: 'sonar-creds', usernameVariable: 'SONAR_HOST_URL', passwordVariable: 'SONAR_LOGIN_TOKEN')]) {
                    withSonarQubeEnv('sonar-server') { 
                        sh """
                        /opt/sonar-scanner/bin/sonar-scanner \
                        -Dsonar.projectKey=python-app \
                        -Dsonar.sources=. \
                        -Dsonar.login=${SONAR_LOGIN_TOKEN} \
                        -Dsonar.host.url=${SONAR_HOST_URL}
                        """
                    }
                }
            }
        }



        stage('Docker Image Build') {
            steps {
                script {
                    sh 'docker system prune -f'
                    sh 'docker container prune -f'
                    sh 'docker build -t ${APP_NAME}:${BUILD_NUMBER} .'
                }
            }
        }

        stage('Test') {
            steps {
                sh 'docker run ${APP_NAME}:${BUILD_NUMBER} python -m pytest || [ $? -eq 5 ] && echo "No tests found"'
            }
        }

        stage('Docker Image Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    script {
                        sh 'ls -la'
                        sh 'pwd'
                        sh 'echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin'
                        sh 'docker tag ${APP_NAME}:${BUILD_NUMBER} ${DOCKER_USERNAME}/${APP_NAME}:${BUILD_NUMBER}'
                        sh 'docker push ${DOCKER_USERNAME}/${APP_NAME}:${BUILD_NUMBER}'
                        sh 'docker logout'
                    }
                }
            }
        }

        stage('Update Config Repo for ArgoCD') {
            steps {
                dir('config-repo') {
                    // Clone the config repo
                    git branch: 'main', url: 'https://github.com/saisanthosh934/santhosh-app-config'
                    
                    // Update the deployment YAML
                    script {
                        def yamlFile = readYaml file: 'kubernetes-manifest/deployment.yaml'
                        yamlFile.spec.template.spec.containers[0].image = "${env.DOCKER_USERNAME}/${env.APP_NAME}:${env.BUILD_NUMBER}"
                        writeYaml file: 'kubernetes-manifest/deployment.yaml', data: yamlFile, overwrite: true
                    }
                    
                    // Commit and push changes
                    withCredentials([usernamePassword(credentialsId: 'GITHUB', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
                        git config user.email "saisanthosh934@gmail.com"
                        git config user.name ${GIT_USER}
                        git add ${env.DEPLOYMENT_FILE}
                        git commit -m "Update image to ${env.BUILD_NUMBER}"
                        git push https://${GIT_USER}:${GIT_PASSWORD}@github.com/saisanthosh934/santhosh-app-config.git main
                        """
                    }
                }
            }
        }

        stage('Sync ArgoCD App') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'argocd-token', variable: 'ARGOCD_TOKEN')]) {
                        sh """
                        curl -X POST \
                        -H "Authorization: Bearer ${ARGOCD_TOKEN}" \
                        -H "Content-Type: application/json" \
                        https://argocd.example.com/api/v1/applications/python-app/sync \
                        -d '{}'
                        """
                    }
                }
            }
        }
    }
}
