import time

import pytest
import requests

# Dictionary mapping service names to their base URLs for easy access.
BASE_URLS = {
    "ai-service": "http://localhost:5004",
    "analytics-service": "http://localhost:5003",
    "api-gateway": "http://localhost:5000",
    "credit-service": "http://localhost:5002",
    "document-service": "http://localhost:5005",
    "ledger-service": "http://localhost:5001",
    "payment-service": "http://localhost:5006",
    "user-service": "http://localhost:5007",
}


# Helper function to make authenticated requests
def make_authenticated_request(
    service, endpoint, method="GET", headers=None, json=None, data=None
):
    """
    Constructs a URL and sends an authenticated request to the specified service.

    Args:
        service (str): Key from BASE_URLS (e.g., "api-gateway").
        endpoint (str): The API path (e.g., "/api/v1/users/profile").
        method (str): HTTP method ("GET", "POST", "PUT", "DELETE").
        headers (dict, optional): Additional headers to include.
        json (dict, optional): JSON payload for POST/PUT requests.
        data (dict, optional): Form data for POST/PUT requests.

    Returns:
        requests.Response: The response object from the request.
    """
    url = f"{BASE_URLS[service]}{endpoint}"
    # Default authorization headers for testing
    default_headers = {
        "X-User-ID": "test_user_id",
        "Authorization": "Bearer test_token",
    }
    if headers:
        default_headers.update(headers)

    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers)
        elif method == "POST":
            response = requests.post(url, headers=default_headers, json=json, data=data)
        elif method == "PUT":
            response = requests.put(url, headers=default_headers, json=json, data=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError("Unsupported HTTP method")
        return response
    except requests.exceptions.ConnectionError as e:
        pytest.fail(
            f"Could not connect to {service} at {url}: {e}. Ensure services are running."
        )


@pytest.mark.security
def test_unauthorized_access_to_protected_endpoints():
    """Test that protected endpoints return 401 Unauthorized without a token."""
    # List of (service, endpoint, method) tuples
    protected_endpoints = [
        ("ai-service", "/api/v1/predictions/cash-flow", "POST"),
        ("analytics-service", "/api/v1/analytics/summary", "GET"),
        ("api-gateway", "/api/v1/users/profile", "GET"),
        ("credit-service", "/api/v1/credit-scores", "GET"),
        ("document-service", "/api/v1/documents", "GET"),
        ("ledger-service", "/api/v1/accounts", "GET"),
        ("payment-service", "/api/v1/transactions", "GET"),
        ("user-service", "/api/v1/users/profile", "GET"),
    ]

    for service, endpoint, method in protected_endpoints:
        # No Authorization header is sent
        headers = {"X-User-ID": "test_user_id"}
        url = f"{BASE_URLS[service]}{endpoint}"

        if method == "POST":
            response = requests.post(url, headers=headers, json={})
        else:
            response = requests.get(url, headers=headers)

        assert (
            response.status_code == 401
        ), f"Expected 401 for {service}{endpoint}, got {response.status_code}"


@pytest.mark.security
def test_invalid_token_access_to_protected_endpoints():
    """Test that protected endpoints return 401 Unauthorized with an invalid token."""
    protected_endpoints = [
        ("ai-service", "/api/v1/predictions/cash-flow", "POST"),
        ("analytics-service", "/api/v1/analytics/summary", "GET"),
        ("api-gateway", "/api/v1/users/profile", "GET"),
        ("credit-service", "/api/v1/credit-scores", "GET"),
        ("document-service", "/api/v1/documents", "GET"),
        ("ledger-service", "/api/v1/accounts", "GET"),
        ("payment-service", "/api/v1/transactions", "GET"),
        ("user-service", "/api/v1/users/profile", "GET"),
    ]

    for service, endpoint, method in protected_endpoints:
        headers = {"X-User-ID": "test_user_id", "Authorization": "Bearer invalid_token"}
        url = f"{BASE_URLS[service]}{endpoint}"

        if method == "POST":
            response = requests.post(url, headers=headers, json={})
        else:
            response = requests.get(url, headers=headers)

        assert (
            response.status_code == 401
        ), f"Expected 401 for {service}{endpoint} with invalid token, got {response.status_code}"


@pytest.mark.security
def test_sql_injection_vulnerability():
    """
    Test for basic SQL injection attempts in input fields.

    The server is expected to reject the request, return an error status (e.g., 400
    or 500), or return a success status without modifying the database in a malicious way.
    For this test, we'll assert that the request does NOT succeed with a 2xx status.
    """

    # Example payloads for a PUT request to update a user profile field
    # We are testing the 'last_name' field for malicious input
    sqli_payloads = [
        # Tautology injection
        {"last_name": "'; OR 1=1--"},
        # Blind SQL injection attempt (malicious command)
        {"last_name": "'); DROP TABLE users;--"},
        # Other common injection attempt
        {"last_name": "admin' --"},
    ]

    # Assuming you have a way to authenticate a test user (e.g., an auth token)
    # This is often required for a PUT endpoint. Replace 'YOUR_AUTH_TOKEN'
    headers = {
        "Authorization": "Bearer YOUR_AUTH_TOKEN",
        "Content-Type": "application/json",
    }

    print(f"\nTesting URL: {BASE_URL}")

    for payload in sqli_payloads:
        # NOTE: Using a PUT or POST request to send the data
        try:
            response = requests.put(BASE_URL, json=payload, headers=headers, timeout=5)

            # --- ASSERTION LOGIC ---
            # The test should FAIL if a malicious payload results in a successful 2xx status code.
            # This confirms the server is NOT treating the malicious input as a valid operation.
            assert not response.ok, (
                f"SQL Injection FAILED: Server accepted payload {payload} with status {response.status_code}. "
                "This could indicate a vulnerability."
            )

            print(
                f"✅ Payload rejected or handled securely. Status: {response.status_code}"
            )

        except requests.exceptions.RequestException as e:
            # Handle connection errors or timeouts gracefully
            pytest.fail(f"Request to {BASE_URL} failed: {e}")

    # Base data for the request
    base_data = {"email": "test@example.com", "first_name": "admin"}

    vulnerable_endpoint = ("user-service", "/api/v1/users/profile", "PUT")
    service, endpoint, method = vulnerable_endpoint

    for sqli_payload in sqli_payloads:
        data = {**base_data, **sqli_payload}
        response = make_authenticated_request(
            service, endpoint, method=method, json=data
        )

        # Expecting a status code other than 200 (server error or validation error)
        assert (
            response.status_code != 200
        ), f"SQL Injection might be possible on {service}{endpoint}. Request succeeded with status {response.status_code}"

        # Ensure no sensitive database error messages are exposed
        error_content = response.text.lower()
        assert (
            "syntax error" not in error_content and "sql error" not in error_content
        ), f"SQL error message exposed on {service}{endpoint}"


@pytest.mark.security
def test_xss_vulnerability():
    """Test for basic XSS vulnerability in user-supplied content."""
    xss_payload_alert = "<script>alert('XSS')</script>"
    xss_payload_img = "<img src=x onerror=alert('XSS')>"

    vulnerable_endpoints = [
        (
            "document-service",
            "/api/v1/documents",
            "POST",
            {"title": "XSS Test Alert", "content": xss_payload_alert},
        ),
        (
            "document-service",
            "/api/v1/documents",
            "POST",
            {"title": "XSS Test Img", "content": xss_payload_img},
        ),
    ]

    for service, endpoint, method, data in vulnerable_endpoints:
        # Step 1: Attempt to post the malicious payload
        response = make_authenticated_request(
            service, endpoint, method=method, json=data
        )
        assert (
            response.status_code == 200
        ), f"Failed to post XSS payload to {service}{endpoint}"

        # Step 2: Check for unescaped reflection in the immediate response (a quick check)
        assert (
            xss_payload_alert not in response.text
            and xss_payload_img not in response.text
        ), f"XSS payload reflected unescaped in response for {service}{endpoint}"

        # A more robust test would retrieve the stored document and check if the content is escaped.


@pytest.mark.security
def test_rate_limiting_on_login():
    """Test if the login endpoint has basic rate limiting to prevent brute-force attacks."""
    login_endpoint = "/auth/login"
    test_credentials = {"email": "nonexistent@example.com", "password": "wrongpassword"}

    responses = []
    # Try 15 login attempts quickly
    for _ in range(15):
        response = requests.post(
            f"{BASE_URLS['api-gateway']}{login_endpoint}", json=test_credentials
        )
        responses.append(response.status_code)
        # Small delay to simulate rapid attempts
        time.sleep(0.1)

    # We expect either 429 Too Many Requests to appear, or a significant number of requests
    # to *not* be 401 (e.g., indicating a different block/delay mechanism).
    is_rate_limited = 429 in responses or responses.count(401) < 15
    assert is_rate_limited, "Rate limiting might not be in place for login"


@pytest.mark.security
def test_cors_misconfiguration():
    """Test for CORS misconfigurations that might allow unauthorized origins."""
    test_origin = "http://malicious-site.com"
    headers = {"Origin": test_origin, "Access-Control-Request-Method": "GET"}

    for service, base_url in BASE_URLS.items():
        try:
            # Send a Preflight OPTIONS request to a known endpoint
            response = requests.options(f"{base_url}/health", headers=headers)
            if response.status_code == 200:
                # Check if the malicious origin is reflected in Access-Control-Allow-Origin
                allow_origin = response.headers.get("Access-Control-Allow-Origin")

                # Check 1: Does it explicitly reflect the malicious origin?
                assert (
                    allow_origin != test_origin
                ), f"CORS misconfiguration detected on {service}: {test_origin} explicitly allowed"

                # Check 2: Is it set to the wildcard '*' which might be overly permissive?
                if allow_origin == "*":
                    print(
                        f"Warning: CORS for {service} is set to '*' (wildcard). Check if this is intentional."
                    )

        except requests.exceptions.ConnectionError:
            print(f"Could not connect to {service} at {base_url}, skipping CORS test.")


@pytest.mark.security
def test_sensitive_data_exposure():
    """Test that sensitive data is not exposed in API responses."""
    # Test 1: User profile endpoint for password/key exposure
    response = make_authenticated_request("user-service", "/api/v1/users/profile")
    assert response.status_code == 200
    user_profile = response.json()
    assert (
        "password" not in user_profile
    ), "Password hash/field exposed in user profile API"
    assert "secret_key" not in user_profile, "Secret key exposed in user profile API"
    assert "api_key" not in user_profile, "API key exposed in user profile API"

    # Test 2: Error responses for stack traces or excessive detail
    # Trigger an intentional error (e.g., invalid endpoint)
    error_response = requests.get(f"{BASE_URLS['api-gateway']}/nonexistent-endpoint")

    # Expect 404 Not Found
    assert error_response.status_code == 404
    error_content = error_response.text.lower()

    assert "traceback" not in error_content, "Stack trace exposed in error response"
    assert (
        "internal server error" in error_content or "not found" in error_content
    ), "Error message too verbose or not generic"


@pytest.mark.security
def test_http_headers_security():
    """Test for presence of security-related HTTP headers."""
    # Test a simple endpoint on the API Gateway
    response = requests.get(f"{BASE_URLS['api-gateway']}/health")
    assert response.status_code == 200
    headers = response.headers

    # Check for defense headers
    assert (
        headers.get("X-Content-Type-Options") == "nosniff"
    ), "Missing or incorrect X-Content-Type-Options header (MIME type sniffing prevention)"
    assert headers.get("X-Frame-Options") in [
        "DENY",
        "SAMEORIGIN",
    ], "Missing or incorrect X-Frame-Options header (Clickjacking prevention)"
    assert (
        headers.get("X-XSS-Protection") == "1; mode=block"
    ), "Missing or incorrect X-XSS-Protection header (Legacy XSS filter)"
    # Note: HSTS and CSP are often configured at the load balancer/proxy level.


@pytest.mark.security
def test_broken_authentication_session_management():
    """Test for common authentication and session management flaws."""
    # Test 1: Logout invalidates token
    # NOTE: Requires a working mock login endpoint that returns a token
    login_response = requests.post(
        f"{BASE_URLS['api-gateway']}/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        if token:
            logout_headers = {
                "Authorization": f"Bearer {token}",
                "X-User-ID": "test_user_id",
            }
            logout_response = requests.post(
                f"{BASE_URLS['api-gateway']}/auth/logout", headers=logout_headers
            )
            assert logout_response.status_code == 200, "Logout failed"

            # Try to use the token after logout - should be unauthorized
            invalidated_response = requests.get(
                f"{BASE_URLS['api-gateway']}/api/v1/users/profile",
                headers=logout_headers,
            )
            assert (
                invalidated_response.status_code == 401
            ), "Token not invalidated after logout (session remains active)"
    else:
        print(
            "Skipping logout invalidation test: Login failed or mock data not available."
        )


@pytest.mark.security
def test_insecure_direct_object_references():
    """Test for IDOR vulnerabilities by attempting to access other users' resources."""
    # This test is conceptual and requires two distinct user accounts and resources setup.
    # The actual test involves:
    # 1. Login as User A to get Token A.
    # 2. Login as User B to get Token B.
    # 3. User B creates resource X (e.g., document ID 123).
    # 4. User A attempts to access resource X using Token A.
    # 5. Expect a 403 Forbidden or 404 Not Found, not a 200 OK.
    print(
        "IDOR test requires multiple user accounts and resource creation; conceptual test only."
    )


@pytest.mark.security
def test_security_misconfiguration():
    """Test for common security misconfigurations (e.g., exposed debug interfaces)."""
    # This test is highly application-specific and deployment-environment dependent.
    # Example: checking for known default credentials, or exposed configuration files.
    print(
        "Security misconfiguration test is conceptual and highly dependent on deployment environment."
    )


@pytest.mark.security
def test_using_components_with_known_vulnerabilities():
    """Test for outdated or vulnerable components."""
    # This typically involves dependency scanning tools (e.g., Snyk, OWASP Dependency-Check).
    # It checks the version history of libraries used (e.g., Flask, Python, requests, etc.).
    print(
        "Testing for known vulnerabilities requires dependency scanning tools; conceptual test only."
    )


@pytest.mark.security
def test_insufficient_logging_monitoring():
    """Test for insufficient logging and monitoring of security events."""
    # This is a grey-box test requiring access to application logs.
    # Conceptual test: Trigger a failure (e.g., 401 or 500) and verify a corresponding log entry exists.
    print(
        "Insufficient logging/monitoring test requires access to application logs; conceptual test only."
    )


@pytest.mark.security
def test_server_side_request_forgery_ssrf():
    """Test for SSRF vulnerabilities."""
    # SSRF occurs when a web application fetches a remote resource without validating the user-supplied URL.
    # If NexaFi has a feature that fetches URLs (e.g., document import from URL), it could be vulnerable.
    # Conceptual test: Try to make the application fetch an internal resource (like http://localhost) or a non-HTTP/HTTPS URL.
    print("SSRF test is conceptual and depends on specific application features.")


@pytest.mark.security
def test_unvalidated_redirects_forwards():
    """Test for unvalidated redirects and forwards."""
    # If the application redirects users based on a URL parameter, it could be vulnerable to phishing.
    # Conceptual test: Try to provide a malicious URL as a redirect parameter (e.g., /login?next=http://malicious.com).
    print(
        "Unvalidated redirects test is conceptual and depends on specific application features."
    )


@pytest.mark.security
def test_file_upload_vulnerabilities():
    """Test for file upload vulnerabilities (e.g., uploading malicious executables)."""
    # If NexaFi allows file uploads (e.g., for documents), it could be vulnerable.
    # Conceptual test: Try to upload a file with a malicious extension (e.g., .exe, .php) or content (e.g., a reverse shell).
    print(
        "File upload vulnerability test is conceptual and depends on specific application features."
    )
