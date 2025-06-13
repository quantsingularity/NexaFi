
import MobileApiClient from \"../../../frontend/mobile/src/lib/mobileApi\";

describe(\"MobileApiClient\", () => {
  let mobileApiClient;
  let mockFetch;

  beforeEach(() => {
    // Mock the global fetch function
    mockFetch = jest.fn();
    global.fetch = mockFetch;

    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    };
    Object.defineProperty(window, \"localStorage\", {
      value: localStorageMock,
    });

    // Re-initialize MobileApiClient to ensure it picks up fresh mocks
    mobileApiClient = new MobileApiClient();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // Helper to create a mock response
  const createMockResponse = (body, options = {}) => {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
      headers: new Headers({ \"content-type\": \"application/json\" }),
      ...options,
    });
  };

  const createMockErrorResponse = (status = 400, statusText = \"Bad Request\") => {
    return Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ error: \"Error message\" }),
      text: () => Promise.resolve(\"Error message\"),
      status,
      statusText,
      headers: new Headers({ \"content-type\": \"application/json\" }),
    });
  };

  test(\"constructor initializes with token from localStorage\", () => {
    localStorage.getItem.mockReturnValueOnce(\"test_token\");
    const newMobileApiClient = new MobileApiClient();
    expect(newMobileApiClient.token).toBe(\"test_token\");
    expect(localStorage.getItem).toHaveBeenCalledWith(\"token\");
  });

  test(\"setToken sets token and stores in localStorage\", () => {
    mobileApiClient.setToken(\"new_token\");
    expect(mobileApiClient.token).toBe(\"new_token\");
    expect(localStorage.setItem).toHaveBeenCalledWith(\"token\", \"new_token\");
  });

  test(\"setToken clears token and localStorage if null\", () => {
    mobileApiClient.setToken(null);
    expect(mobileApiClient.token).toBeNull();
    expect(localStorage.removeItem).toHaveBeenCalledWith(\"token\");
  });

  test(\"getHeaders returns correct headers with token\", () => {
    mobileApiClient.setToken(\"test_token\");
    const headers = mobileApiClient.getHeaders();
    expect(headers.Authorization).toBe(\"Bearer test_token\");
    expect(headers[\"Content-Type\"]).toBe(\"application/json\");
  });

  test(\"getHeaders returns correct headers without token\", () => {
    const headers = mobileApiClient.getHeaders();
    expect(headers.Authorization).toBeUndefined();
    expect(headers[\"Content-Type\"]).toBe(\"application/json\");
  });

  test(\"request makes a GET request and returns JSON\", async () => {
    const mockData = { message: \"Success\" };
    mockFetch.mockImplementationOnce(() => createMockResponse(mockData));

    const result = await mobileApiClient.request(\"/test\");
    expect(mockFetch).toHaveBeenCalledWith(
      \"http://localhost:5000/test\",
      {
        headers: { \"Content-Type\": \"application/json\" },
      }
    );
    expect(result).toEqual(mockData);
  });

  test(\"request handles 401 error by clearing token and redirecting\", async () => {
    mockFetch.mockImplementationOnce(() => createMockErrorResponse(401));
    const originalLocation = window.location;
    delete window.location;
    window.location = { href: \"\" };

    try {
      await mobileApiClient.request(\"/protected\");
    } catch (error) {
      // Expected to catch an error, but the primary action is redirect
    }

    expect(localStorage.removeItem).toHaveBeenCalledWith(\"token\");
    expect(window.location.href).toBe(\"/auth\");
    window.location = originalLocation; // Restore original location
  });

  test(\"login sends correct data and returns response\", async () => {
    const mockResponse = { success: true, token: \"abc\" };
    mockFetch.mockImplementationOnce(() => createMockResponse(mockResponse));

    const credentials = { email: \"test@example.com\", password: \"password123\" };
    const result = await mobileApiClient.login(credentials);

    expect(mockFetch).toHaveBeenCalledWith(
      \"http://localhost:5000/auth/login\",
      {
        method: \"POST\",
        body: JSON.stringify(credentials),
        headers: { \"Content-Type\": \"application/json\" },
      }
    );
    expect(result).toEqual(mockResponse);
  });

  test(\"logout clears token and calls API\", async () => {
    mobileApiClient.setToken(\"some_token\");
    mockFetch.mockImplementationOnce(() => createMockResponse({ message: \"Logged out\" }));

    await mobileApiClient.logout();

    expect(mockFetch).toHaveBeenCalledWith(
      \"http://localhost:5000/auth/logout\",
      {
        method: \"POST\",
        headers: { \"Content-Type\": \"application/json\", \"Authorization\": \"Bearer some_token\" },
      }
    );
    expect(localStorage.removeItem).toHaveBeenCalledWith(\"token\");
  });

  test(\"getCachedData retrieves data from localStorage\", () => {
    localStorage.getItem.mockReturnValueOnce(JSON.stringify({ data: \"cached_value\" }));
    const result = mobileApiClient.getCachedData(\"test_key\");
    expect(localStorage.getItem).toHaveBeenCalledWith(\"cache_test_key\");
    expect(result).toEqual({ data: \"cached_value\" });
  });

  test(\"setCachedData stores data in localStorage\", () => {
    const dataToCache = { item: \"value\" };
    mobileApiClient.setCachedData(\"new_key\", dataToCache);
    expect(localStorage.setItem).toHaveBeenCalledWith(\"cache_new_key\", JSON.stringify(dataToCache));
  });

  test(\"clearCache removes all \"cache_\" prefixed items\", () => {
    localStorage.getItem.mockImplementation((key) => {
      if (key === \"cache_item1\" || key === \"cache_item2\" || key === \"other_item\") {
        return \"some_value\";
      }
      return null;
    });
    Object.defineProperty(localStorage, \"keys\", {
      value: jest.fn(() => [\"cache_item1\", \"cache_item2\", \"other_item\"]),
    });

    mobileApiClient.clearCache();

    expect(localStorage.removeItem).toHaveBeenCalledWith(\"cache_item1\");
    expect(localStorage.removeItem).toHaveBeenCalledWith(\"cache_item2\");
    expect(localStorage.removeItem).not.toHaveBeenCalledWith(\"other_item\");
  });
});


