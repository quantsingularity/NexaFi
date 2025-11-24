import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../../../frontend/web/src/App";
import {
  AuthProvider,
  AppProvider,
} from "../../../frontend/web/src/contexts/AppContext";

// --- Mock useAuth ONLY ---
jest.mock("../../../frontend/web/src/contexts/AppContext", () => {
  const actual = jest.requireActual(
    "../../../frontend/web/src/contexts/AppContext",
  );
  return {
    ...actual,
    useAuth: jest.fn(),
  };
});

const mockUseAuth =
  require("../../../frontend/web/src/contexts/AppContext").useAuth;

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
    logout: jest.fn(),
  });

  return render(
    <AppProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </AppProvider>,
  );
};

describe("App Routing and Authentication", () => {
  test("renders Homepage on '/' when NOT authenticated", () => {
    renderApp(["/"], false);
    expect(screen.getByText(/Welcome to NexaFi/i)).toBeInTheDocument();
  });

  test("redirects /auth -> /dashboard when authenticated", () => {
    renderApp(["/auth"], true);
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
  });

  test("renders AuthPage for /auth when NOT authenticated", () => {
    renderApp(["/auth"], false);
    expect(screen.getByText(/Sign In/i)).toBeInTheDocument();
  });

  test("renders dashboard when visiting /dashboard while authenticated", () => {
    renderApp(["/dashboard"], true);
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
  });

  test("redirects /dashboard -> /auth when NOT authenticated", () => {
    renderApp(["/dashboard"], false);
    expect(screen.getByText(/Sign In/i)).toBeInTheDocument();
  });

  test("shows loading screen when auth state is loading", () => {
    renderApp(["/dashboard"], false, true);
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });
});
