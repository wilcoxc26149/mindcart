pipeline {
  // Built-in Docker controller is Linux — bat stages need the Windows host agent.
  agent { label 'windows-host' }

  environment {
    PYTHONUNBUFFERED = '1'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Setup') {
      steps {
        bat '''
          if not exist .venv (
            python -m venv .venv
          )
          if not exist artifacts mkdir artifacts
          call .venv\\Scripts\\activate.bat
          python -m pip install -U pip
          pip install -e ".[dev]"
        '''
      }
    }

    stage('Unit tests') {
      steps {
        bat '''
          call .venv\\Scripts\\activate.bat
          python -m pytest -q --junitxml=artifacts\\junit.xml
        '''
      }
    }

    stage('E2E tests') {
      steps {
        bat '''
          call .venv\\Scripts\\activate.bat
          python -m pytest -q --run-e2e tests\\test_e2e_cognee_host.py --junitxml=artifacts\\junit-e2e.xml
        '''
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'artifacts/junit*.xml'
    }
    failure {
      echo 'MindCart CI failed. Check venv setup or pytest output.'
    }
  }
}
