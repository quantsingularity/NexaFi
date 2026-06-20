import * as matchers from "@testing-library/jest-dom/matchers";
import { cleanup } from "@testing-library/react";
import { afterEach, expect, vi } from "vitest";

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

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

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock navigator.onLine
Object.defineProperty(navigator, "onLine", {
  writable: true,
  value: true,
});

// Mock IntersectionObserver (used by some UI primitives)
global.IntersectionObserver = class IntersectionObserver {
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
};

// Mock ResizeObserver (used by recharts and some Radix primitives)
global.ResizeObserver = class ResizeObserver {
  disconnect() {}
  observe() {}
  unobserve() {}
};

// jsdom cannot parse some modern (Tailwind v4) CSS injected via <style> tags.
// Filter only that specific noise; leave all other console errors intact.
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
