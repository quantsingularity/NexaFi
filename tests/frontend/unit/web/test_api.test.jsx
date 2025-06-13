
import ApiClient from \"../../../frontend/web/src/lib/api\";

describe(\"ApiClient\", () => {
  let apiClient;
  let mockFetch;

  beforeEach(() => {
    // Mock the global fetch function
    mockFetch = jest.fn();
    global.fetch = mockFetch;

    // Clear localStorage before each test
    localStorage.clear();

    // Re-initialize ApiClient to ensure it picks up fresh mocks and localStorage
    apiClient = new ApiClient();
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

  const createMockErrorResponse = (errorBody, status = 400, statusText = \"Bad Request\") => {
    return Promise.resolve({
      ok: false,
      json: () => Promise.resolve(errorBody),
      text: () => Promise.resolve(JSON.stringify(errorBody)),
      status,
      statusText,
      headers: new Headers({ \"content-type\": \"application/json\" }),
    });
  };

  test(\"constructor initializes with token from localStorage\", () => {
    localStorage.setItem(\"access_token\", \"test_token\");
    const newApiClient = new ApiClient();
    expect(newApiClient.token).toBe(\"test_token\");
  });

  test(\"setToken sets token and stores in localStorage\", () => {
    apiClient.setToken(\"new_token\");
    expect(apiClient.token).toBe(\"new_token\");
    expect(localStorage.getItem(\"access_token\")).toBe(\"new_token\");
  });

  test(\"setToken clears token and localStorage if null\", () => {
    localStorage.setItem(\"access_token\", \"existing_token\");
    apiClient.setToken(null);
    expect(apiClient.token).toBeNull();
    expect(localStorage.getItem(\"access_token\")).toBeNull();
  });

  test(\"getHeaders returns correct headers with token\", () => {
    apiClient.setToken(\"test_token\");
    const headers = apiClient.getHeaders();
    expect(headers[\"Authorization\"]).toBe(\"Bearer test_token\");
    expect(headers[\"Content-Type\"]).toBe(\"application/json\");
  });

  test(\"getHeaders returns correct headers without token\", () => {
    const headers = apiClient.getHeaders();
    expect(headers[\"Authorization\"]).toBeUndefined();
    expect(headers[\"Content-Type\"]).toBe(\"application/json\");
  });

  test(\"request makes a GET request and returns JSON\", async () => {
    const mockData = { message: \"Success\" };
    mockFetch.mockImplementationOnce(() => createMockResponse(mockData));

    const result = await apiClient.request(\"/test\");
    expect(mockFetch).toHaveBeenCalledWith(
      \"http://localhost:5000/api/v1/test\",

