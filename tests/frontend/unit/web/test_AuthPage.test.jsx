import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AuthPage from "../../../frontend/web/src/components/AuthPage";
import {
  AppProvider,
  AuthProvider,
} from "../../../frontend/web/src/contexts/AppContext";

// Mock useAuth
jest.mock("../../../frontend/web/src/contexts/AppContext", () => ({
  ...jest.requireActual("../../../frontend/web/src/contexts/AppContext"),
  useAuth: jest.fn(),
}));

const mockUseAuth =
  require("../../../frontend/web/src/contexts/AppContext").useAuth;

const renderAuthPage = (authProps = {}) => {
  mockUseAuth.mockReturnValue({
    login: jest.fn(),
    register: jest.fn(),
    loading: false,
    error: null,
    clearError: jest.fn(),
    ...authProps,
  });

  return render(
    <AppProvider>
      <AuthProvider>
        <MemoryRouter>
          <AuthPage />
        </MemoryRouter>
      </AuthProvider>
    </AppProvider>,
  );
};

describe("AuthPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders login form by default", () => {
    renderAuthPage();

    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign In/i }),
    ).toBeInTheDocument();
  });

  test("switches to register tab", () => {
    renderAuthPage();

    // This matches MUI roles
    fireEvent.click(screen.getByRole("tab", { name: /Sign Up/i }));

    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Create Account/i }),
    ).toBeInTheDocument();
  });

  test("submits login form", async () => {
    const mockLogin = jest.fn(() => Promise.resolve({ success: true }));

    renderAuthPage({ login: mockLogin });

    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: "secret123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Sign In/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "secret123",
      });
    });
  });

  test("submits register form", async () => {
    const mockRegister = jest.fn(() => Promise.resolve({ success: true }));

    renderAuthPage({ register: mockRegister });

    fireEvent.click(screen.getByRole("tab", { name: /Sign Up/i }));

    fireEvent.change(screen.getByLabelText(/First Name/i), {
      target: { value: "John" },
    });
    fireEvent.change(screen.getByLabelText(/Last Name/i), {
      target: { value: "Doe" },
    });
    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: "john@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), {
      target: { value: "password123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Create Account/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        first_name: "John",
        last_name: "Doe",
        email: "john@example.com",
        password: "password123",
        confirm_password: "password123",
      });
    });
  });

  test("shows backend error", async () => {
    renderAuthPage({
      error: "Invalid credentials",
    });

    expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
  });

  test("password visibility toggle works", () => {
    renderAuthPage();

    const password = screen.getByLabelText(/Password/i);
    const toggle = screen.getByRole("button", {
      name: /toggle password visibility/i,
    });

    expect(password.type).toBe("password");

    fireEvent.click(toggle);
    expect(password.type).toBe("text");

    fireEvent.click(toggle);
    expect(password.type).toBe("password");
  });
});
