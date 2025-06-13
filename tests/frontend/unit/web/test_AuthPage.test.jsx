
import { render, screen, fireEvent, waitFor } from \"@testing-library/react\";
import { MemoryRouter } from \"react-router-dom\";
import AuthPage from \"../../../frontend/web/src/components/AuthPage\";
import { AuthProvider, AppProvider } from \"../../../frontend/web/src/contexts/AppContext\";

// Mock the useAuth hook
jest.mock(\"../../../frontend/web/src/contexts/AppContext\", () => ({
  ...jest.requireActual(\"../../../frontend/web/src/contexts/AppContext\"),
  useAuth: jest.fn(),
}));

const mockUseAuth = require(\"../../../frontend/web/src/contexts/AppContext\").useAuth;

const renderAuthPage = (authProps = {}) => {
  mockUseAuth.mockReturnValue({
    login: jest.fn(),
    register: jest.fn(),
    loading: false,
    error: null,
    clearError: jest.fn(),
    ...authProps,
  });

  render(
    <AppProvider>
      <AuthProvider>
        <MemoryRouter>
          <AuthPage />
        </MemoryRouter>
      </AuthProvider>
    </AppProvider>
  );
};

describe(\"AuthPage\",

