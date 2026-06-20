import js from "@eslint/js";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";

export default [
  { ignores: ["dist", "coverage"] },
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    plugins: {
      react,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // Treat identifiers used in JSX (for example <motion.div> or <Icon />)
      // as used, so no-unused-vars does not report false positives.
      "react/jsx-uses-vars": "error",
      "react/jsx-uses-react": "off",
      "no-unused-vars": [
        "error",
        {
          varsIgnorePattern: "^[A-Z_]",
          argsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  },
  {
    // Build/config files run under Node.
    files: ["*.config.js", "vite.config.js", "vitest.config.js"],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
  {
    // Test files run under Vitest with Node globals available.
    files: [
      "**/*.{test,spec}.{js,jsx}",
      "**/__tests__/**/*.{js,jsx}",
      "**/tests/**/*.{js,jsx}",
      "**/test/**/*.{js,jsx}",
    ],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.vitest,
        vi: "readonly",
      },
    },
  },
];
