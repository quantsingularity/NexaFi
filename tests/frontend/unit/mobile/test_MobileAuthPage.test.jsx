// ✅ Mock MUST come before imports of components that use the hook
jest.mock("../../../frontend/mobile/src/contexts/MobileContext", () => {
  const actual = jest.requireActual(
    "../../../frontend/mobile/src/contexts/MobileContext",
  );
  return {
    ...actual,
    useAuth: jest.fn(),
  };
});

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import MobileAuthPage from "../../../frontend/mobile/src/components/MobileAuthPage";
import {
  MobileProviders,
  useAuth,
} from "../../../frontend/mobile/src/contexts/MobileContext";

const mockUseAuth = useAuth;

const renderMobileAuthPage = (authProps = {}) => {
  mockUseAuth.mockReturnValue({
    login: jest.fn(),
    register: jest.fn(),
    loading: false,
    error: null,
    ...authProps,
  });

  render(
    <MobileProviders>
      <MemoryRouter>
        <MobileAuthPage />
      </MemoryRouter>
    </MobileProviders>,
  );
};

describe("MobileAuthPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders login form by default", () => {
    renderMobileAuthPage();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign In/i }),
    ).toBeInTheDocument();
  });

  test("switches to register form when Sign Up tab is clicked", () => {
    renderMobileAuthPage();
    fireEvent.click(screen.getByRole("tab", { name: /Sign Up/i }));

    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Business Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Create Account/i }),
    ).toBeInTheDocument();
  });

  test("handles login form submission", async () => {
    const mockLogin = jest.fn(() => Promise.resolve({ success: true }));
    renderMobileAuthPage({ login: mockLogin });

    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: "password123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Sign In/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
    });
  });

  test("handles registration form submission", async () => {
    const mockRegister = jest.fn(() => Promise.resolve({ success: true }));
    renderMobileAuthPage({ register: mockRegister });

    fireEvent.click(screen.getByRole("tab", { name: /Sign Up/i }));

    fireEvent.change(screen.getByLabelText(/First Name/i), {
      target: { value: "John" },
    });
    fireEvent.change(screen.getByLabelText(/Last Name/i), {
      target: { value: "Doe" },
    });
    fireEvent.change(screen.getByLabelText(/^Email$/i), {
      target: { value: "john.doe@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/Business Name/i), {
      target: { value: "Acme Corp" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Create Account/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        first_name: "John",
        last_name: "Doe",
        email: "john.doe@example.com",
        password: "password123",
        confirm_password: "password123",
        business_name: "Acme Corp",
        phone: "",
      });
    });
  });

  test("displays error message on login failure", async () => {
    const mockLogin = jest.fn(() =>
      Promise.resolve({ success: false, error: "Invalid credentials" }),
    );

    renderMobileAuthPage({ login: mockLogin });

    fireEvent.change(screen.getByLabelText(/Email/i), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: "wrongpassword" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Sign In/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  test("displays error message when registration passwords do not match", async () => {
    renderMobileAuthPage();

    fireEvent.click(screen.getByRole("tab", { name: /Sign Up/i }));

    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), {
      target: { value: "passwordABC" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Create Account/i }));

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });

  test("toggles password visibility", () => {
    renderMobileAuthPage();

    const passwordInput = screen.getByLabelText(/^Password$/i);

    // Support multiple possible aria-labels
    const toggleButton =
      screen.queryByLabelText(/show password/i) ||
      screen.queryByLabelText(/hide password/i) ||
      screen.getByRole("button", { name: /toggle/i });

    expect(passwordInput.type).toBe("password");
    fireEvent.click(toggleButton);
    expect(passwordInput.type).toBe("text");
    fireEvent.click(toggleButton);
    expect(passwordInput.type).toBe("password");
  });
});
