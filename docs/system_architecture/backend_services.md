# Backend Services

NexaFi's backend is composed of several independent microservices, each designed to handle specific functionalities within the financial technology domain. This section provides detailed documentation for each service, outlining its purpose, key features, API endpoints, data models, and operational considerations.

## 1. API Gateway Service

*   **Purpose**: The API Gateway acts as the single entry point for all client requests, routing them to the appropriate backend microservices. It handles cross-cutting concerns such as authentication, authorization, rate limiting, and load balancing.
*   **Technology Stack**: Flask, Python
*   **Key Features**:
    *   Dynamic service discovery and routing.
    *   Centralized authentication and authorization using JWTs.
    *   Request and response transformation.
    *   Health checks for backend services.
*   **API Endpoints**: All external API calls are routed through the API Gateway. Specific routes are then forwarded to individual services.
    *   `/api/v1/auth/*`: Routes related to user authentication (e.g., login, registration).
    *   `/api/v1/users/*`: Routes for user profile management.
    *   `/api/v1/payments/*`: Routes for payment processing.
    *   `/api/v1/ledger/*`: Routes for transaction history.
    *   `/api/v1/credit/*`: Routes for credit-related operations.
    *   `/api/v1/analytics/*`: Routes for financial analytics and reporting.
    *   `/api/v1/documents/*`: Routes for document management.
*   **Data Models**: The API Gateway primarily handles request and response schemas, ensuring data consistency across services. It does not persist its own core business data.
*   **Configuration**: Configured via environment variables for service URLs and security keys.

## 2. User Service

*   **Purpose**: Manages all user-related functionalities, including user registration, authentication, profile management, and account settings.
*   **Technology Stack**: Flask, Python, PostgreSQL
*   **Key Features**:
    *   Secure user registration and login.
    *   User profile creation and updates.
    *   Password management (hashing, reset).
    *   Role-based access control (RBAC).
*   **API Endpoints**:
    *   `POST /api/v1/auth/register`: Register a new user.
    *   `POST /api/v1/auth/login`: Authenticate user and issue JWT.
    *   `GET /api/v1/users/{user_id}`: Retrieve user profile by ID.
    *   `PUT /api/v1/users/{user_id}`: Update user profile.
    *   `DELETE /api/v1/users/{user_id}`: Deactivate or delete user account.
*   **Data Models**: `User` (id, username, email, password_hash, roles, created_at, updated_at), `Profile` (user_id, first_name, last_name, address, phone_number).
*   **Database**: PostgreSQL, with tables for `users` and `profiles`.

## 3. Payment Service

*   **Purpose**: Handles all aspects of payment processing, including initiating payments, managing payment methods, and tracking payment statuses.
*   **Technology Stack**: Flask, Python, PostgreSQL
*   **Key Features**:
    *   Secure payment initiation and execution.
    *   Support for various payment methods (e.g., bank transfers, credit/debit cards).
    *   Transaction validation and fraud checks.
    *   Integration with external payment gateways.
*   **API Endpoints**:
    *   `POST /api/v1/payments/initiate`: Initiate a new payment.
    *   `GET /api/v1/payments/{payment_id}`: Retrieve payment details by ID.
    *   `PUT /api/v1/payments/{payment_id}/status`: Update payment status.
    *   `POST /api/v1/payments/methods`: Add a new payment method.
    *   `GET /api/v1/payments/methods/{user_id}`: Retrieve user's payment methods.
*   **Data Models**: `Payment` (id, user_id, amount, currency, status, method, transaction_id, created_at), `PaymentMethod` (id, user_id, type, details).
*   **Database**: PostgreSQL, with tables for `payments` and `payment_methods`.

## 4. Ledger Service

*   **Purpose**: Maintains an immutable, auditable record of all financial transactions within the NexaFi platform. It acts as the single source of truth for all financial movements.
*   **Technology Stack**: Flask, Python, PostgreSQL
*   **Key Features**:
    *   Immutable transaction logging.
    *   Double-entry accounting principles for financial integrity.
    *   Querying of transaction history.
    *   Ensuring data consistency and auditability.
*   **API Endpoints**:
    *   `POST /api/v1/ledger/transactions`: Record a new transaction (typically called internally by other services).
    *   `GET /api/v1/ledger/transactions/{user_id}`: Retrieve transaction history for a user.
    *   `GET /api/v1/ledger/transactions/{transaction_id}`: Retrieve details of a specific transaction.
*   **Data Models**: `Transaction` (id, user_id, type, amount, currency, description, timestamp, related_entity_id).
*   **Database**: PostgreSQL, with a table for `transactions`.

## 5. Credit Service

*   **Purpose**: Manages credit-related functionalities, including credit scoring, loan application processing, and credit line management.
*   **Technology Stack**: Flask, Python, PostgreSQL, (potentially integrates with ML models for scoring)
*   **Key Features**:
    *   Credit score calculation and management.
    *   Loan application submission and approval workflow.
    *   Credit line assignment and monitoring.
    *   Integration with external credit bureaus (if applicable).
*   **API Endpoints**:
    *   `POST /api/v1/credit/applications`: Submit a loan application.
    *   `GET /api/v1/credit/applications/{application_id}`: Retrieve loan application status.
    *   `GET /api/v1/credit/score/{user_id}`: Retrieve user's credit score.
    *   `PUT /api/v1/credit/lines/{user_id}`: Update user's credit line.
*   **Data Models**: `LoanApplication` (id, user_id, amount, status, application_date), `CreditScore` (user_id, score, last_updated), `CreditLine` (user_id, limit, available).
*   **Database**: PostgreSQL, with tables for `loan_applications`, `credit_scores`, and `credit_lines`.

## 6. Analytics Service

*   **Purpose**: Processes and analyzes financial data to provide insights, generate reports, and support business intelligence. It consumes data from other services, often via message queues.
*   **Technology Stack**: Flask, Python, PostgreSQL, (potentially integrates with data warehousing solutions)
*   **Key Features**:
    *   Real-time and batch data processing.
    *   Generation of financial reports (e.g., spending patterns, income analysis).
    *   Dashboard data aggregation.
    *   Data visualization support.
*   **API Endpoints**:
    *   `GET /api/v1/analytics/spending/{user_id}`: Get spending analysis for a user.
    *   `GET /api/v1/analytics/income/{user_id}`: Get income analysis for a user.
    *   `GET /api/v1/analytics/reports/{report_type}`: Generate various financial reports.
*   **Data Models**: Primarily aggregates and transforms data from other services. May have its own materialized views or summary tables.
*   **Database**: PostgreSQL, potentially with a data warehouse for large-scale analytics.

## 7. AI Service

*   **Purpose**: Integrates machine learning models to provide intelligent features such as fraud detection, personalized financial advice, or predictive analytics.
*   **Technology Stack**: Flask, Python, TensorFlow/PyTorch, (potentially specialized ML serving frameworks)
*   **Key Features**:
    *   Fraud detection using supervised/unsupervised learning.
    *   Personalized financial recommendations.
    *   Predictive modeling for market trends.
    *   Model deployment and serving.
*   **API Endpoints**:
    *   `POST /api/v1/ai/fraud-check`: Check for potential fraud in a transaction.
    *   `GET /api/v1/ai/recommendations/{user_id}`: Get personalized financial recommendations.
    *   `POST /api/v1/ai/predict-trend`: Predict financial trends.
*   **Data Models**: Input/output schemas for ML models. May store model metadata or inference results.
*   **Database**: May use a database for storing model versions, training data, or inference logs.

## 8. Document Service

*   **Purpose**: Manages the secure storage, retrieval, and processing of user documents, such as KYC (Know Your Customer) documents, identity proofs, or financial statements.
*   **Technology Stack**: Flask, Python, (potentially integrates with object storage like S3)
*   **Key Features**:
    *   Secure document upload and download.
    *   Document versioning.
    *   Access control for sensitive documents.
    *   Integration with OCR (Optical Character Recognition) for document parsing.
*   **API Endpoints**:
    *   `POST /api/v1/documents/upload`: Upload a new document.
    *   `GET /api/v1/documents/{document_id}`: Retrieve a document by ID.
    *   `DELETE /api/v1/documents/{document_id}`: Delete a document.
    *   `GET /api/v1/documents/user/{user_id}`: List documents for a user.
*   **Data Models**: `Document` (id, user_id, filename, file_type, storage_path, uploaded_at, status).
*   **Storage**: Typically uses secure object storage (e.g., AWS S3, Google Cloud Storage) for actual file storage, with metadata stored in a database.


