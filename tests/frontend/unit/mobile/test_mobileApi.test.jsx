import MobileApiClient from "../../../frontend/mobile/src/lib/mobileApi";

describe("MobileApiClient", () => {
  let mobileApiClient;
  let mockFetch;

  beforeEach(() => {
    // Mock global fetch
    mockFetch = jest.fn();
    global.fetch = mockFetch;

    // Properly mock localStorage with enumerable keys
    const store = {};

    const localStorageMock = {
      getItem: jest.fn((key) => store[key] || null),
      setItem: jest.fn((key, value) => {
        store[key] = value;
      }),
      removeItem: jest.fn((key) => {
        delete store[key];
      }),
      clear: jest.fn(() => {
        Object.keys(store).forEach((key) => delete store[key]);
      }),
      // ensure Object.keys(localStorage) works
      get length() {
        return Object.keys(store).length;
      },
      key: jest.fn((index) => Object.keys(store)[index] || null),

      // This makes our fake keys enumerable
      _store: store,
    };

    Object.defineProperty(window, "localStorage", {
      value: localStorageMock,
      writable: true,
    });

    mobileApiClient = new MobileApiClient();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const createMockResponse = (body, options = {}) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
      headers: new Headers({ "content-type": "application/json" }),
      ...options,
    });

  const createMockErrorResponse = (status = 400, statusText = "Bad Request") =>
    Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ error: "Error message" }),
      text: () => Promise.resolve("Error message"),
      status,
      statusText,
      headers: new Headers({ "content-type": "application/json" }),
    });

  test("constructor initializes with token from localStorage", () => {
    window.localStorage.getItem.mockReturnValueOnce("test_token");
    const newMobileApiClient = new MobileApiClient();
    expect(newMobileApiClient.token).toBe("test_token");
    expect(window.localStorage.getItem).toHaveBeenCalledWith("token");
  });

  test("setToken sets token and stores in localStorage", () => {
    mobileApiClient.setToken("new_token");
    expect(mobileApiClient.token).toBe("new_token");
    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      "token",
      "new_token",
    );
  });

  test("setToken clears token and localStorage if null", () => {
    mobileApiClient.setToken(null);
    expect(mobileApiClient.token).toBeNull();
    expect(window.localStorage.removeItem).toHaveBeenCalledWith("token");
  });

  test("getHeaders returns correct headers with token", () => {
    mobileApiClient.setToken("test_token");
    const headers = mobileApiClient.getHeaders();
    expect(headers.Authorization).toBe("Bearer test_token");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  test("getHeaders returns correct headers without token", () => {
    const headers = mobileApiClient.getHeaders();
    expect(headers.Authorization).toBeUndefined();
    expect(headers["Content-Type"]).toBe("application/json");
  });

  test("request makes a GET request and returns JSON", async () => {
    const mockData = { message: "Success" };
    mockFetch.mockImplementationOnce(() => createMockResponse(mockData));

    const result = await mobileApiClient.request("/test");

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:5000/test", {
      headers: { "Content-Type": "application/json" },
    });

    expect(result).toEqual(mockData);
  });

  test("request handles 401 error by clearing token and redirecting", async () => {
    mockFetch.mockImplementationOnce(() => createMockErrorResponse(401));

    const originalLocation = window.location;
    delete window.location;

    window.location = { href: "" };

    await expect(mobileApiClient.request("/protected")).rejects.toBeTruthy();

    expect(window.localStorage.removeItem).toHaveBeenCalledWith("token");
    expect(window.location.href).toBe("/auth");

    window.location = originalLocation;
  });

  test("login sends correct data and returns response", async () => {
    const mockResponse = { success: true, token: "abc" };
    mockFetch.mockImplementationOnce(() => createMockResponse(mockResponse));

    const credentials = { email: "test@example.com", password: "password123" };

    const result = await mobileApiClient.login(credentials);

    expect(mockFetch).toHaveBeenCalledWith("http://localhost:5000/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
      headers: { "Content-Type": "application/json" },
    });

    expect(result).toEqual(mockResponse);
  });

  test("logout clears token and calls API", async () => {
    mobileApiClient.setToken("some_token");

    mockFetch.mockImplementationOnce(() =>
      createMockResponse({ message: "Logged out" }),
    );

    await mobileApiClient.logout();

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:5000/auth/logout",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer some_token",
        },
      },
    );

    expect(window.localStorage.removeItem).toHaveBeenCalledWith("token");
  });

  test("getCachedData retrieves data from localStorage", () => {
    window.localStorage.getItem.mockReturnValueOnce(
      JSON.stringify({ data: "cached_value" }),
    );
    const result = mobileApiClient.getCachedData("test_key");

    expect(window.localStorage.getItem).toHaveBeenCalledWith("cache_test_key");
    expect(result).toEqual({ data: "cached_value" });
  });

  test("setCachedData stores data in localStorage", () => {
    const dataToCache = { item: "value" };

    mobileApiClient.setCachedData("new_key", dataToCache);

    expect(window.localStorage.setItem).toHaveBeenCalledWith(
      "cache_new_key",
      JSON.stringify(dataToCache),
    );
  });

  test('clearCache removes all "cache_" prefixed items', () => {
    window.localStorage._store["cache_item1"] = "x";
    window.localStorage._store["cache_item2"] = "y";
    window.localStorage._store["other_item"] = "z";

    mobileApiClient.clearCache();

    expect(window.localStorage.removeItem).toHaveBeenCalledWith("cache_item1");
    expect(window.localStorage.removeItem).toHaveBeenCalledWith("cache_item2");
    expect(window.localStorage.removeItem).not.toHaveBeenCalledWith(
      "other_item",
    );
  });
});
