# GitHub Actions Workflows for NexaFi

This directory (`.github/workflows/`) contains the Continuous Integration (CI) and Continuous Deployment (CD) workflows for the NexaFi project, powered by GitHub Actions. These workflows automate the processes of building, testing, and deploying various components of the NexaFi platform, ensuring code quality, consistency, and efficient delivery.

## Workflow Overview

The following GitHub Actions workflow files are defined in this directory:

- `frontend_ci_cd.yml`: Handles CI/CD for the frontend application.
- `backend_ci_cd.yml`: Manages CI/CD for the backend services.
- `ml_ci_cd.yml`: Orchestrates CI/CD for the machine learning components.
- `cd_pipeline.yml`: A consolidated CD pipeline that can be triggered by successful CI runs of other components (though currently, deployment logic is embedded within individual CI/CD files for simplicity).
- `frontend_ci.yml`: (Legacy/Specific) A basic CI workflow for the frontend, potentially superseded by `frontend_ci_cd.yml`.
- `backend_ci.yml`: (Legacy/Specific) A basic CI workflow for the backend, potentially superseded by `backend_ci_cd.yml`.

Each workflow is designed to be modular, focusing on a specific part of the NexaFi ecosystem. They are triggered automatically based on code changes in their respective directories.

## Detailed Workflow Descriptions

### `frontend_ci_cd.yml` - Frontend CI/CD Pipeline

This workflow automates the build, test, and deployment process for the NexaFi frontend application. It ensures that any changes made to the frontend codebase are thoroughly validated before being deployed.

- **Purpose**: To provide continuous integration and continuous deployment for the frontend application.
- **Triggers**:
  - `push` events to the `main` branch, specifically when changes occur within the `frontend/` directory.
  - `pull_request` events targeting the `main` branch, also limited to changes within the `frontend/` directory.
- **Jobs**:
  - `build-and-test`:
    - **Runs on**: `ubuntu-latest`
    - **Steps**:
      1.  `Checkout repository`: Fetches the code from the repository.
      2.  `Set up Node.js`: Configures the Node.js environment (version `18`).
      3.  `Install dependencies`: Installs all necessary npm packages defined in `frontend/package.json`.
      4.  `Run Tests`: Executes frontend tests (e.g., `npm test`).
      5.  `Build frontend`: Builds the production-ready frontend application (`npm run build`).
      6.  `Upload build artifact`: Archives the `frontend/build` directory as an artifact named `frontend-build`, making it available for subsequent jobs or workflows.
  - `deploy`:
    - **Runs on**: `ubuntu-latest`
    - **Dependencies**: Requires the `build-and-test` job to complete successfully.
    - **Condition**: Only runs if the current branch is `main` (`github.ref == 'refs/heads/main'`).
    - **Steps**:
      1.  `Checkout repository`: Fetches the code again.
      2.  `Download frontend build artifact`: Retrieves the `frontend-build` artifact created by the `build-and-test` job.
      3.  `Deploy to production`: This is a placeholder step. In a real-world scenario, this would contain commands to deploy the built frontend to a static hosting service (e.g., Netlify, Vercel, GitHub Pages), an S3 bucket, or via a cloud provider's CLI.

### `backend_ci_cd.yml` - Backend CI/CD Pipeline

This workflow handles the CI/CD process for the NexaFi backend services. It automates testing, linting, and deployment of the backend codebase.

- **Purpose**: To provide continuous integration and continuous deployment for the backend services.
- **Triggers**:
  - `push` events to the `main` branch, specifically when changes occur within the `backend/` directory.
  - `pull_request` events targeting the `main` branch, also limited to changes within the `backend/` directory.
- **Jobs**:
  - `build-and-test`:
    - **Runs on**: `ubuntu-latest`
    - **Steps**:
      1.  `Checkout repository`: Fetches the code.
      2.  `Set up Python`: Configures the Python environment (version `3.9`).
      3.  `Install dependencies`: Installs Python packages from `backend/requirements.txt`.
      4.  `Run Linting (Flake8)`: Installs and runs Flake8 to check for code style and quality issues.
      5.  `Run Tests`: Executes backend tests (e.g., `python manage.py test`).
      6.  `Archive production artifacts`: Archives the entire `backend/` directory as an artifact named `backend-build`.
  - `deploy`:
    - **Runs on**: `ubuntu-latest`
    - **Dependencies**: Requires the `build-and-test` job to complete successfully.
    - **Condition**: Only runs if the current branch is `main`.
    - **Steps**:
      1.  `Checkout repository`: Fetches the code.
      2.  `Download backend build artifact`: Retrieves the `backend-build` artifact.
      3.  `Deploy to production`: This is a placeholder step. Actual deployment logic would involve SSHing into a server, using cloud provider CLIs (e.g., AWS CLI, Azure CLI, gcloud CLI), or interacting with CI/CD tools like ArgoCD, Spinnaker, or Jenkins.

### `ml_ci_cd.yml` - Machine Learning CI/CD Pipeline

This workflow is dedicated to the CI/CD of the machine learning components, including model testing and deployment.

- **Purpose**: To provide continuous integration and continuous deployment for the machine learning models and related code.
- **Triggers**:
  - `push` events to the `main` branch, specifically when changes occur within the `ml/` directory.
  - `pull_request` events targeting the `main` branch, also limited to changes within the `ml/` directory.
- **Jobs**:
  - `build-and-test`:
    - **Runs on**: `ubuntu-latest`
    - **Steps**:
      1.  `Checkout repository`: Fetches the code.
      2.  `Set up Python`: Configures the Python environment (version `3.9`).
      3.  `Install dependencies`: Installs Python packages from `ml/requirements.txt`.
      4.  `Run Tests`: Executes ML-specific tests (e.g., `python -m pytest`).
      5.  `Archive model artifacts`: Archives the `ml/models/` directory as an artifact named `ml-models`.
  - `deploy`:
    - **Runs on**: `ubuntu-latest`
    - **Dependencies**: Requires the `build-and-test` job to complete successfully.
    - **Condition**: Only runs if the current branch is `main`.
    - **Steps**:
      1.  `Checkout repository`: Fetches the code.
      2.  `Download model artifacts`: Retrieves the `ml-models` artifact.
      3.  `Deploy ML models`: This is a placeholder step. Actual deployment logic would involve pushing models to a model registry (e.g., MLflow, Sagemaker), updating serving endpoints, or triggering data pipelines.

### `cd_pipeline.yml` - Consolidated CD Pipeline (Placeholder)

This workflow is intended as a higher-level CD pipeline that could potentially orchestrate deployments after successful runs of the individual component CI/CD workflows. Currently, the deployment logic is primarily handled within the `deploy` jobs of `frontend_ci_cd.yml`, `backend_ci_cd.yml`, and `ml_ci_cd.yml`.

- **Purpose**: To serve as a central point for triggering and monitoring deployments across different components.
- **Triggers**:
  - `workflow_run` events, specifically when the `Frontend CI` or `Backend CI` workflows complete.
- **Jobs**:
  - `deploy`:
    - **Runs on**: `ubuntu-latest`
    - **Dependencies**: Needs `frontend_deploy` and `backend_deploy` (these are currently placeholder jobs within this workflow).
    - **Condition**: Only runs if the triggering workflow run was successful.
    - **Steps**:
      1.  `Checkout repository`: Fetches the code.
      2.  `Download frontend build artifact`: Placeholder for downloading frontend artifacts.
      3.  `Trigger Frontend Deployment`: Placeholder for triggering frontend deployment scripts.
      4.  `Trigger Backend Deployment`: Placeholder for triggering backend deployment scripts.
  - `frontend_deploy`:
    - **Runs on**: `ubuntu-latest`
    - **Condition**: Runs if the triggering workflow was `Frontend CI` and it succeeded.
    - **Steps**: Placeholder for frontend deployment logic.
  - `backend_deploy`:
    - **Runs on**: `ubuntu-latest`
    - **Condition**: Runs if the triggering workflow was `Backend CI` and it succeeded.
    - **Steps**: Placeholder for backend deployment logic.

**Note**: For a more robust and scalable CD setup, consider using dedicated deployment tools or services (e.g., ArgoCD, Spinnaker, Jenkins, cloud-native deployment services) that integrate with GitHub Actions.

### `frontend_ci.yml` - Basic Frontend CI (Legacy)

This is a simpler CI workflow for the frontend, primarily focused on building the application and uploading artifacts. It is largely superseded by `frontend_ci_cd.yml` which includes testing and deployment steps.

- **Purpose**: Basic continuous integration for the frontend.
- **Triggers**: Similar to `frontend_ci_cd.yml` but for basic CI.
- **Jobs**:
  - `build`:
    - **Runs on**: `ubuntu-latest`
    - **Steps**: Checkout, Node.js setup, dependency installation, frontend build, and artifact upload.

### `backend_ci.yml` - Basic Backend CI (Legacy)

Similar to `frontend_ci.yml`, this is a basic CI workflow for the backend, focused on building and testing. It is largely superseded by `backend_ci_cd.yml`.

- **Purpose**: Basic continuous integration for the backend.
- **Triggers**: Similar to `backend_ci_cd.yml` but for basic CI.
- **Jobs**:
  - `build`:
    - **Runs on**: `ubuntu-latest`
    - **Steps**: Checkout, Python setup, dependency installation, and running tests.

## How to Use and Contribute

- **Understanding Workflows**: Review the `.yml` files to understand the exact steps and conditions for each pipeline.
- **Customization**: Modify the workflow files to fit specific deployment targets, testing frameworks, or additional steps required for your project.
- **Adding New Workflows**: For new services or components, create a new `.yml` file in this directory, following the existing patterns.
- **Troubleshooting**: GitHub Actions provides detailed logs for each workflow run. If a workflow fails, check the logs for specific error messages.

For more information on GitHub Actions, refer to the [official documentation](https://docs.github.com/en/actions).
