/**
 * Mobile App Routing + Auth Tests
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// --- Mock useAuth BEFORE importing App or MobileProviders ---
jest.mock("../../../frontend/mobile/src/contexts/MobileContext", () => {
  const actual = jest.requireActual(
    "../../../frontend/mobile/src/contexts/MobileContext",
  );

  return {
    ...actual,
    useAuth: jest.fn(), // mock hook
  };
});

// Now import after the mock is set up
import App from "../../../frontend/mobile/src/App";
import {
  MobileProviders,
  useAuth,
} from "../../../frontend/mobile/src/contexts/MobileContext";

// local hook ref for convenience
const mockUseAuth = useAuth;

const renderApp = (
  initialEntries = ["/"],
  isAuthenticated = false,
  loading = false,
) => {
  mockUseAuth.mockReturnValue({
    isAuthenticated,
    loading,
    user: isAuthenticated ? { id: "123", email: "test@example.com" } : null,
    login: jest.fn(),
    register: jest.fn(),
  });

  render(
    <MobileProviders>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </MobileProviders>,
  );
};

describe("Mobile App Routing and Authentication", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders MobileHomepage for "/" route when not authenticated', () => {
    renderApp(["/"]);
    expect(screen.getByText(/Welcome to NexaFi Mobile/i)).toBeInTheDocument();
  });

  test("redirects from /auth to /dashboard if authenticated", () => {
    renderApp(["/auth"], true);
    expect(screen.getByText(/Mobile Dashboard Content/i)).toBeInTheDocument();
  });

  test("renders MobileAuthPage for /auth when NOT authenticated", () => {
    renderApp(["/auth"], false);
    expect(screen.getByText(/Mobile Sign In/i)).toBeInTheDocument();
  });
});
