# Getting Started

This section provides a comprehensive guide to setting up your development environment and getting the NexaFi application up and running locally. Follow these steps to ensure a smooth setup process.

## Prerequisites

Before you begin, ensure you have the following software installed on your system:

*   **Git**: For cloning the repository.
*   **Docker and Docker Compose**: For containerizing and orchestrating the microservices.
*   **Python 3.9+**: For backend services development.
*   **Node.js 18+ and npm/yarn**: For frontend development.

## 1. Clone the Repository

First, clone the NexaFi repository from GitHub:

```bash
git clone https://github.com/abrar2030/NexaFi.git
cd NexaFi
```

## 2. Environment Configuration

Each service in NexaFi might require specific environment variables. Navigate to each service directory (e.g., `backend/api-gateway`, `backend/user-service`, `frontend/web`) and look for `.env.example` files. Copy these files to `.env` and update the values as per your local environment setup.

Example for `backend/api-gateway/.env`:

```
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your_api_gateway_secret_key
USER_SERVICE_URL=http://localhost:5001
ANALYTICS_SERVICE_URL=http://localhost:5002
# Add other service URLs as needed
```

## 3. Backend Setup

NexaFi's backend is composed of several Flask microservices. You can run them individually or use Docker Compose for a more integrated setup.

### Using Docker Compose (Recommended)

Navigate to the root of the `NexaFi` directory and run:

```bash
docker-compose up --build
```

This command will build the Docker images for all services (if not already built) and start them. This is the easiest way to get all backend services running with their dependencies.

### Running Services Individually

If you prefer to run services individually for development or debugging:

1.  **Install Python Dependencies**: For each backend service (e.g., `backend/user-service`, `backend/api-gateway`):

    ```bash
    cd backend/user-service
    pip install -r requirements.txt
    ```

2.  **Run the Service**: After installing dependencies, you can run the service:

    ```bash
    python src/main.py
    ```

    Repeat this for all necessary backend services.

## 4. Frontend Setup

NexaFi includes both web and mobile frontend applications.

### Web Application

1.  **Navigate to Web Directory**:

    ```bash
    cd frontend/web
    ```

2.  **Install Node.js Dependencies**:

    ```bash
    npm install # or yarn install
    ```

3.  **Start the Development Server**:

    ```bash
    npm start # or yarn start
    ```

    The web application should now be accessible at `http://localhost:3000` (or another port if configured).

### Mobile Application

(Instructions for mobile application setup will be provided here, depending on the framework used, e.g., React Native, Flutter, etc.)

## 5. Database Setup

NexaFi services typically use PostgreSQL databases. When running with Docker Compose, databases are usually set up automatically. If running services individually, you might need to set up local PostgreSQL instances and configure connection strings in the `.env` files.

## 6. Initial Data Population

Some services might require initial data for proper functioning. Refer to individual service documentation for details on data migration or seeding scripts.

## Troubleshooting

*   **Port Conflicts**: If you encounter port conflicts, ensure no other applications are using the ports required by NexaFi services (e.g., 5000, 5001, 3000).
*   **Dependency Issues**: Double-check that all `requirements.txt` and `package.json` dependencies are correctly installed.
*   **Environment Variables**: Verify that all necessary environment variables are set correctly in the `.env` files.

If you face any issues not covered here, please refer to the specific service documentation or open an issue on the GitHub repository.
