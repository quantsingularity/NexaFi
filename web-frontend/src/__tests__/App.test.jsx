import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import App from "../App";

// Mock the contexts
vi.mock("../contexts/AppContext", () => ({
  AuthProvider: ({ children }) => <div>{children}</div>,
  AppProvider: ({ children }) => <div>{children}</div>,
  useAuth: () => ({
    isAuthenticated: false,
    loading: false,
    user: null,
  }),
}));

// Mock components to avoid complex rendering
vi.mock("../components/AuthPage", () => ({
  default: () => <div>Auth Page</div>,
}));

vi.mock("../components/Dashboard", () => ({
  default: () => <div>Dashboard</div>,
}));

describe("App Component", () => {
  it("renders without crashing", () => {
    render(<App />);
    expect(document.querySelector(".App")).toBeTruthy();
  });
});
