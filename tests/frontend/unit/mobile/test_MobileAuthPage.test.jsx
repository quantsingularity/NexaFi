
import { render, screen, fireEvent, waitFor } from \"@testing-library/react\";
import { MemoryRouter } from \"react-router-dom\";
import MobileAuthPage from \"../../../frontend/mobile/src/components/MobileAuthPage\";
import { MobileProviders } from \"../../../frontend/mobile/src/contexts/MobileContext\";

// Mock the useAuth hook
jest.mock(\"../../../frontend/mobile/src/contexts/MobileContext\", () => ({
  ...jest.requireActual(\"../../../frontend/mobile/src/contexts/MobileContext\"),
  useAuth: jest.fn(),
}));

const mockUseAuth = require(\"../../../frontend/mobile/src/contexts/MobileContext\").useAuth;

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
    </MobileProviders>
  );
};

describe(\"MobileAuthPage\", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test(\"renders login form by default\", () => {
    renderMobileAuthPage();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole(\"button\", { name: /Sign In/i })).toBeInTheDocument();
  });

  test(\"switches to register form when Sign Up tab is clicked\", () => {
    renderMobileAuthPage();
    fireEvent.click(screen.getByRole(\"tab\", { name: /Sign Up/i }));
    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Business Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(screen.getByRole(\"button\", { name: /Create Account/i })).toBeInTheDocument();
  });

  test(\"handles login form submission\", async () => {
    const mockLogin = jest.fn(() => Promise.resolve({ success: true }));
    renderMobileAuthPage({ login: mockLogin });

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: \"test@example.com\" } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: \"password123\" } });
    fireEvent.click(screen.getByRole(\"button\", { name: /Sign In/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: \"test@example.com\",
        password: \"password123\",
      });
    });
  });

  test(\"handles registration form submission\", async () => {
    const mockRegister = jest.fn(() => Promise.resolve({ success: true }));
    renderMobileAuthPage({ register: mockRegister });

    fireEvent.click(screen.getByRole(\"tab\", { name: /Sign Up/i }));

    fireEvent.change(screen.getByLabelText(/First Name/i), { target: { value: \"John\" } });
    fireEvent.change(screen.getByLabelText(/Last Name/i), { target: { value: \"Doe\" } });
    fireEvent.change(screen.getByLabelText(/register-email/i), { target: { value: \"john.doe@example.com\" } });
    fireEvent.change(screen.getByLabelText(/register-password/i), { target: { value: \"password123\" } });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: \"password123\" } });
    fireEvent.change(screen.getByLabelText(/Business Name/i), { target: { value: \"Acme Corp\" } });

    fireEvent.click(screen.getByRole(\"button\", { name: /Create Account/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        first_name: \"John\",
        last_name: \"Doe\",
        email: \"john.doe@example.com\",
        password: \"password123\",
        confirm_password: \"password123\",
        business_name: \"Acme Corp\",
        phone: \"\", // phone is optional and not filled in this test
      });
    });
  });

  test(\"displays error message on login failure\", async () => {
    const mockLogin = jest.fn(() => Promise.resolve({ success: false, error: \"Invalid credentials\" }));
    renderMobileAuthPage({ login: mockLogin });

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: \"test@example.com\" } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: \"wrongpassword\" } });
    fireEvent.click(screen.getByRole(\"button\", { name: /Sign In/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  test(\"displays error message on registration password mismatch\", async () => {
    renderMobileAuthPage();
    fireEvent.click(screen.getByRole(\"tab\", { name: /Sign Up/i }));

    fireEvent.change(screen.getByLabelText(/register-password/i), { target: { value: \"password123\" } });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: \"passwordabc\" } });
    fireEvent.click(screen.getByRole(\"button\", { name: /Create Account/i }));

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });

  test(\"toggles password visibility\", () => {
    renderMobileAuthPage();
    const passwordInput = screen.getByLabelText(/Password/i);
    const toggleButton = screen.getByRole(\"button\", { name: /toggle password visibility/i });

    expect(passwordInput.getAttribute(\"type\")).toBe(\"password\");
    fireEvent.click(toggleButton);
    expect(passwordInput.getAttribute(\"type\")).toBe(\"text\");
    fireEvent.click(toggleButton);
    expect(passwordInput.getAttribute(\"type\")).toBe(\"password\");
  });
});
