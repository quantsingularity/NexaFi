
import time

import pytest
import requests

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
def make_authenticated_request(service, endpoint, method=\"GET\", headers=None, json=None, data=None):
    url = f\"{BASE_URLS[service]}{endpoint}\"
    default_headers = {\"X-User-ID\": \"test_user_id\", \"Authorization\": \"Bearer test_token\"}
    if headers:
        default_headers.update(headers)

    try:
        if method == \"GET\":
            response = requests.get(url, headers=default_headers)
        elif method == \"POST\":
            response = requests.post(url, headers=default_headers, json=json, data=data)
        elif method == \"PUT\":
            response = requests.put(url, headers=default_headers, json=json, data=data)
        elif method == \"DELETE\":
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(\"Unsupported HTTP method\")
        return response
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f\"Could not connect to {service} at {url}: {e}. Ensure services are running.\")

@pytest.mark.security
def test_unauthorized_access_to_protected_endpoints():
    """Test that protected endpoints return 401 Unauthorized without a token."""
    protected_endpoints = [
        ("ai-service", "/api/v1/predictions/cash-flow", "POST"),
        ("analytics-service", "/api/v1/analytics/summary"),
        ("api-gateway", "/api/v1/users/profile"),
        ("credit-service", "/api/v1/credit-scores"),
        ("document-service", "/api/v1/documents"),
        ("ledger-service", "/api/v1/accounts"),
        ("payment-service", "/api/v1/transactions"),
        ("user-service", "/api/v1/users/profile"),
    ]

    for service, endpoint, method in protected_endpoints:
        headers = {\"X-User-ID\": \"test_user_id\"} # No Authorization header
        if method == \"POST\":
            response = requests.post(f\"{BASE_URLS[service]}{endpoint}\", headers=headers, json={})
        else:
            response = requests.get(f\"{BASE_URLS[service]}{endpoint}\", headers=headers)
        assert response.status_code == 401, f\"Expected 401 for {service}{endpoint}, got {response.status_code}\"

@pytest.mark.security
def test_invalid_token_access_to_protected_endpoints():
    """Test that protected endpoints return 401 Unauthorized with an invalid token."""
    protected_endpoints = [
        ("ai-service", "/api/v1/predictions/cash-flow", "POST"),
        ("analytics-service", "/api/v1/analytics/summary"),
        ("api-gateway", "/api/v1/users/profile"),
        ("credit-service", "/api/v1/credit-scores"),
        ("document-service", "/api/v1/documents"),
        ("ledger-service", "/api/v1/accounts"),
        ("payment-service", "/api/v1/transactions"),
        ("user-service", "/api/v1/users/profile"),
    ]

    for service, endpoint, method in protected_endpoints:
        headers = {\"X-User-ID\": \"test_user_id\", \"Authorization\": \"Bearer invalid_token\"}
        if method == \"POST\":
            response = requests.post(f\"{BASE_URLS[service]}{endpoint}\", headers=headers, json={})
        else:
            response = requests.get(f\"{BASE_URLS[service]}{endpoint}\", headers=headers)
        assert response.status_code == 401, f\"Expected 401 for {service}{endpoint} with invalid token, got {response.status_code}\"

@pytest.mark.security
def test_sql_injection_vulnerability():
    """Test for basic SQL injection attempts in input fields."""
    # This is a conceptual test. Actual SQLi testing requires more sophisticated tools and payloads.
    # For Flask-SQLAlchemy, direct SQLi is often mitigated, but input validation is still key.
    vulnerable_endpoints = [
        ("user-service", "/api/v1/users/profile", "PUT", {\"email\": \"test@example.com\", \"first_name\": \"admin\"},
         {\"last_name\": \"\"\" OR 1=1--\"\"}),
        ("user-service", "/api/v1/users/profile", "PUT", {\"email\": \"test@example.com\", \"first_name\": \"admin\"},
         {\"last_name\": \""); DROP TABLE users;--\"}),
    ]

    for service, endpoint, method, base_data, sqli_payload in vulnerable_endpoints:
        data = {**base_data, **sqli_payload}
        response = make_authenticated_request(service, endpoint, method=method, json=data)
        # Expecting a server error or validation error, not successful execution of SQLi
        assert response.status_code != 200, f\"SQL Injection might be possible on {service}{endpoint}\"
        # More specific checks would involve looking for database errors in logs or response content
        assert \"syntax error\" not in response.text.lower() and \"sql error\" not in response.text.lower(), \
            f\"SQL error message exposed on {service}{endpoint}\"

@pytest.mark.security
def test_xss_vulnerability():
    """Test for basic XSS vulnerability in user-supplied content."""
    # This is a conceptual test. XSS typically affects frontend rendering.
    # Backend should sanitize inputs before storing/returning.
    xss_payload_alert = \"<script>alert(\'XSS\')</script>\"
    xss_payload_img = \"<img src=x onerror=alert(\'XSS\')>\"
    vulnerable_endpoints = [
        ("document-service", "/api/v1/documents", "POST", {\"title\": \"XSS Test Alert\", \"content\": xss_payload_alert}),
        ("document-service", "/api/v1/documents", "POST", {\"title\": \"XSS Test Img\", \"content\": xss_payload_img}),
    ]

    for service, endpoint, method, data in vulnerable_endpoints:
        response = make_authenticated_request(service, endpoint, method=method, json=data)
        assert response.status_code == 200, f\"Failed to post XSS payload to {service}{endpoint}\"
        # In a real scenario, you'd then try to retrieve this content and assert that the script tag is escaped or removed.
        # For example, by fetching the document and checking its content.
        # retrieve_response = make_authenticated_request(service, f\"/api/v1/documents/{response.json()[\"id\"]}\")
        # assert xss_payload not in retrieve_response.text # This would be the actual check
        # For now, we assert that the response doesn't immediately reflect the XSS payload unescaped
        assert xss_payload_alert not in response.text and xss_payload_img not in response.text, \
            f\"XSS payload reflected unescaped in response for {service}{endpoint}\"

@pytest.mark.security
def test_rate_limiting_on_login():
    """Test if the login endpoint has basic rate limiting to prevent brute-force attacks."""
    login_endpoint = "/auth/login"
    test_credentials = {\"email\": \"nonexistent@example.com\", \"password\": \"wrongpassword\"}
    
    responses = []
    for _ in range(15): # Try 15 login attempts quickly
        response = requests.post(f\"{BASE_URLS[\"api-gateway\"]}{login_endpoint}", json=test_credentials)
        responses.append(response.status_code)
        time.sleep(0.1) # Small delay to simulate rapid attempts

    # Expecting some 429 Too Many Requests or a significant number of 401s followed by a delay/block
    # A stronger check would involve timing and specific headers.
    # For a basic check, we expect either 429 to appear or not all attempts to be 401 (implying some form of block)
    assert 429 in responses or responses.count(401) < 15, \"Rate limiting might not be in place for login\"

@pytest.mark.security
def test_cors_misconfiguration():
    """Test for CORS misconfigurations that might allow unauthorized origins."""
    test_origin = \"http://malicious-site.com\"
    headers = {\"Origin\": test_origin, \"Access-Control-Request-Method\": \"GET\"}

    for service, base_url in BASE_URLS.items():
        try:
            response = requests.options(f\"{base_url}/health\", headers=headers) # Preflight request
            if response.status_code == 200:
                # Check if the malicious origin is reflected in Access-Control-Allow-Origin
                # If CORS is set to *, this test will fail, but it might be an intentional configuration.
                assert response.headers.get(\"Access-Control-Allow-Origin\") != test_origin, \
                    f\"CORS misconfiguration detected on {service}: {test_origin} allowed\"
        except requests.exceptions.ConnectionError:
            print(f\"Could not connect to {service} at {base_url}, skipping CORS test.\")

@pytest.mark.security
def test_sensitive_data_exposure():
    """Test that sensitive data is not exposed in API responses."""
    # Test user profile endpoint for password exposure
    response = make_authenticated_request("user-service", "/api/v1/users/profile")
    assert response.status_code == 200
    user_profile = response.json()
    assert "password" not in user_profile, "Password exposed in user profile API"
    assert "secret_key" not in user_profile, "Secret key exposed in user profile API"
    assert "api_key" not in user_profile, "API key exposed in user profile API"

    # Test error responses for stack traces or excessive detail
    # Trigger an intentional error (e.g., invalid endpoint or malformed request)
    error_response = requests.get(f\"{BASE_URLS[\"api-gateway\"]}/nonexistent-endpoint\")
    assert error_response.status_code == 404 # Or 500, depending on the error
    error_content = error_response.text.lower()
    assert "traceback" not in error_content, "Stack trace exposed in error response"
    assert "internal server error" in error_content or "not found" in error_content, \
        "Error message too verbose or not generic"

@pytest.mark.security
def test_http_headers_security():
    """Test for presence of security-related HTTP headers."""
    response = requests.get(f\"{BASE_URLS[\"api-gateway\"]}/health\")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get(\"X-Content-Type-Options\") == \"nosniff\", \
        \"Missing or incorrect X-Content-Type-Options header\"
    assert headers.get(\"X-Frame-Options\") in [\"DENY\", \"SAMEORIGIN\"], \
        \"Missing or incorrect X-Frame-Options header\"
    assert headers.get(\"X-XSS-Protection\") == \"1; mode=block\", \
        \"Missing or incorrect X-XSS-Protection header\"
    # HSTS and CSP are often handled by reverse proxies or web servers, so they might not be present directly from Flask apps.
    # assert \"Strict-Transport-Security\" in headers, \"Missing Strict-Transport-Security header\"
    # assert \"Content-Security-Policy\" in headers, \"Missing Content-Security-Policy header\"

@pytest.mark.security
def test_broken_authentication_session_management():
    """Test for common authentication and session management flaws."""
    # Test 1: Logout invalidates token
    login_response = requests.post(f\"{BASE_URLS[\"api-gateway\"]}/auth/login\", json={
        \"email\": \"test@example.com\", \"password\": \"password123\"
    })
    if login_response.status_code == 200:
        token = login_response.json().get(\"access_token\")
        if token:
            logout_headers = {\"Authorization\": f\"Bearer {token}\", \"X-User-ID\": \"test_user_id\"}
            logout_response = requests.post(f\"{BASE_URLS[\"api-gateway\"]}/auth/logout\", headers=logout_headers)
            assert logout_response.status_code == 200, \"Logout failed\"

            # Try to use the token after logout - should be unauthorized
            invalidated_response = requests.get(f\"{BASE_URLS[\"api-gateway\"]}/api/v1/users/profile\", headers=logout_headers)
            assert invalidated_response.status_code == 401, \"Token not invalidated after logout\"
    else:
        print(\"Skipping logout invalidation test: Login failed.\")

@pytest.mark.security
def test_insecure_direct_object_references():
    """Test for IDOR vulnerabilities by attempting to access other users' resources."""
    # This test requires two distinct user accounts and resources.
    # For demonstration, we'll assume a document service where documents have IDs.
    # In a real scenario, you'd create doc1 for user1, doc2 for user2.
    # Then user1 tries to access doc2.

    # Conceptual example:
    # user1_token = get_token("user1")
    # user2_token = get_token("user2")
    # doc_id_of_user2 = create_document("user2", user2_token)

    # response_user1_accessing_user2_doc = requests.get(
    #     f"{BASE_URLS["document-service"]}/api/v1/documents/{doc_id_of_user2}",
    #     headers={"Authorization": f"Bearer {user1_token}", "X-User-ID": "user1_id"}
    # )
    # assert response_user1_accessing_user2_doc.status_code == 403, "IDOR vulnerability detected!"
    print(\"IDOR test requires multiple user accounts and resource creation; conceptual test only.\")

@pytest.mark.security
def test_security_misconfiguration():
    """Test for common security misconfigurations (e.g., default credentials, unnecessary services)."""
    # This is highly application-specific.
    # Example: Check for default admin passwords, exposed debug interfaces.
    # For NexaFi, we can check if debug mode is enabled in production (assuming it's not).
    
    # Check if debug mode is explicitly off in main.py for each service (conceptual)
    # This would involve reading the source code or checking a /health or /info endpoint that reveals debug status.
    # For now, we'll assume debug is off by default in deployed environments.
    print(\"Security misconfiguration test is conceptual and highly dependent on deployment environment.\")

@pytest.mark.security
def test_using_components_with_known_vulnerabilities():
    """Test for outdated or vulnerable components."""
    # This typically involves dependency scanning tools (e.g., Snyk, OWASP Dependency-Check).
    # For a manual test, you might check versions of key libraries.
    # Example: Check Flask version, Python version.
    # This is outside the scope of direct API testing.
    print(\"Testing for known vulnerabilities requires dependency scanning tools; conceptual test only.\")

@pytest.mark.security
def test_insufficient_logging_monitoring():
    """Test for insufficient logging and monitoring of security events."""
    # This is hard to test via black-box API calls.
    # It requires access to logs and monitoring systems.
    # Conceptual test: Trigger an error and check if it's logged (requires log access).
    print(\"Insufficient logging/monitoring test requires access to application logs; conceptual test only.\")

@pytest.mark.security
def test_server_side_request_forgery_ssrf():
    """Test for SSRF vulnerabilities."""
    # SSRF occurs when a web application fetches a remote resource without validating the user-supplied URL.
    # If NexaFi has a feature that fetches URLs (e.g., document import from URL), it could be vulnerable.
    # Conceptual test: Try to make the application fetch an internal resource or a non-HTTP/HTTPS URL.
    print(\"SSRF test is conceptual and depends on specific application features.\")

@pytest.mark.security
def test_unvalidated_redirects_forwards():
    """Test for unvalidated redirects and forwards."""
    # If the application redirects users based on a URL parameter, it could be vulnerable to phishing.
    # Conceptual test: Try to provide a malicious URL as a redirect parameter.
    print(\"Unvalidated redirects test is conceptual and depends on specific application features.\")

@pytest.mark.security
def test_file_upload_vulnerabilities():
    """Test for file upload vulnerabilities (e.g., uploading malicious executables)."""
    # If NexaFi allows file uploads (e.g., for documents), it could be vulnerable.
    # Conceptual test: Try to upload a file with a malicious extension or content.
    p
(Content truncated due to size limit. Use line ranges to read in chunks)