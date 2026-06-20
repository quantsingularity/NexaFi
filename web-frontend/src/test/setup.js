import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  disconnect() {}
  observe() {}
  unobserve() {}
};

// jsdom cannot parse some modern (Tailwind v4) CSS that components inject via
// <style> tags. The error is harmless in tests and only adds noise, so filter
// out that specific message while leaving all other console errors intact.
const originalConsoleError = console.error;
console.error = (...args) => {
  const first = args[0];
  if (
    typeof first === "string" &&
    first.includes("Could not parse CSS stylesheet")
  ) {
    return;
  }
  if (first instanceof Error && first.message.includes("Could not parse CSS")) {
    return;
  }
  originalConsoleError(...args);
};
