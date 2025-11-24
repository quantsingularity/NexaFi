import ApiClient from "../../../frontend/web/src/lib/api";

describe("ApiClient", () => {
  let apiClient;
  let mockFetch;

  beforeEach(() => {
    mockFetch = jest.fn();
    global.fetch = mockFetch;

    localStorage.clear();

    apiClient = new ApiClient();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const createMockResponse = (body, options = {}) => {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
      headers: new Headers({ "content-type": "application/json" }),
      ...options,
    });
  };

  const createMockErrorResponse = (
    errorBody,
    status = 400,
    statusText = "Bad Request",
  ) => {
    return Promise.resolve({
      ok: false,
      status,
      statusText,
      json: () => Promise.resolve(errorBody),
      text: () => Promise.resolve(JSON.stringify(errorBody)),
      headers: new Headers({ "content-type": "application/json" }),
    });
  };

  // ---------------------------------------------
  // TOKEN TESTS
  // ---------------------------------------------

  test("constructor initializes with token from localStorage", () => {
    localStorage.setItem("access_token", "test_token");
    const newClient = new ApiClient();
    expect(newClient.token).toBe("test_token");
  });

  test("setToken stores token in memory + localStorage", () => {
    apiClient.setToken("new_token");
    expect(apiClient.token).toBe("new_token");
    expect(localStorage.getItem("access_token")).toBe("new_token");
  });

  test("setToken(null) clears token + storage", () => {
    localStorage.setItem("access_token", "foo");
    apiClient.setToken(null);

    expect(apiClient.token).toBeNull();
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  // ---------------------------------------------
  // HEADER TESTS
  // ---------------------------------------------

  test("getHeaders returns correct headers with token", () => {
    apiClient.setToken("abc123");
    const headers = apiClient.getHeaders();

    expect(headers["Authorization"]).toBe("Bearer abc123");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  test("getHeaders returns headers without Authorization if no token", () => {
    const headers = apiClient.getHeaders();
    expect(headers["Authorization"]).toBeUndefined();
    expect(headers["Content-Type"]).toBe("application/json");
  });

  // ---------------------------------------------
  // REQUEST TESTS
  // ---------------------------------------------

  test("request performs a GET and returns JSON", async () => {
    const mockData = { message: "Success" };
    mockFetch.mockImplementationOnce(() => createMockResponse(mockData));

    const result = await apiClient.request("/test");

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:5000/api/v1/test",
      expect.objectContaining({
        method: "GET",
        headers: expect.any(Object),
      }),
    );

    expect(result).toEqual(mockData);
  });

  test("request sends POST with JSON body", async () => {
    const mockData = { message: "created" };

    mockFetch.mockImplementationOnce(() => createMockResponse(mockData));

    const body = { name: "Item" };

    const result = await apiClient.request("/items", "POST", body);

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:5000/api/v1/items",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(body),
      }),
    );

    expect(result).toEqual(mockData);
  });

  test("request handles text responses when not JSON", async () => {
    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        text: () => Promise.resolve("plain text response"),
        headers: new Headers({ "content-type": "text/plain" }),
      }),
    );

    const result = await apiClient.request("/plain");

    expect(result).toBe("plain text response");
  });

  test("request throws error on non-OK status with JSON error body", async () => {
    const errorBody = { error: "Something failed" };

    mockFetch.mockImplementationOnce(() =>
      createMockErrorResponse(errorBody, 400),
    );

    await expect(apiClient.request("/fail")).rejects.toEqual({
      status: 400,
      statusText: "Bad Request",
      ...errorBody,
    });
  });

  test("request throws error when fetch itself rejects", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network failure"));

    await expect(apiClient.request("/boom")).rejects.toThrow("Network failure");
  });
});
