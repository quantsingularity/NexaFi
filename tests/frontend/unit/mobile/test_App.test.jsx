
import { render, screen } from \"@testing-library/react\";
import { MemoryRouter } from \"react-router-dom\";
import App from \"../../../frontend/mobile/src/App\";
import { MobileProviders, useAuth } from \"../../../frontend/mobile/src/contexts/MobileContext\";

// Mock the useAuth hook to control authentication state
jest.mock(\"../../../frontend/mobile/src/contexts/MobileContext\", () => ({
  ...jest.requireActual(\"../../../frontend/mobile/src/contexts/MobileContext\"),
  useAuth: jest.fn(),
}));

const mockUseAuth = require(\"../../../frontend/mobile/src/contexts/MobileContext\").useAuth;

const renderApp = (initialEntries = [\"/\"], isAuthenticated = false, loading = false) => {
  mockUseAuth.mockReturnValue({
    isAuthenticated,
    loading,
    user: isAuthenticated ? { id: \"123\", email: \"test@example.com\" } : null,
    login: jest.fn(),
    register: jest.fn(),
  });

  render(
    <MobileProviders>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </MobileProviders>
  );
};

describe(\"Mobile App Routing and Authentication\", () => {
  test(\"renders MobileHomepage for \"/\" route when not authenticated\", () => {
    renderApp([\"/\"]);
    expect(screen.getByText(/Welcome to NexaFi Mobile/i)).toBeInTheDocument();
  });

  test(\"redirects from /auth to /dashboard if authenticated\", () => {
    renderApp([\"/auth\"], true);
    expect(screen.getByText(/Mobile Dashboard Content/i)).toBeInTheDocument(); // Assuming MobileDashboard has this text
  });

  test(\"renders MobileAuthPage for /auth route when not authenticated\", () => {
    renderApp([\"/auth\"]);
    expect(screen.getByText(/Mobile Sign In/i)).toBeInTheDocument(); // Assuming MobileAuthPage has a 

