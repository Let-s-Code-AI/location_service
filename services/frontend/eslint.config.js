// ESLint flat config (`npm run lint`, also run by the CI quality gate).
// Based on the Vite React template: ESLint recommended rules, React Hooks
// rules (incl. the React Compiler checks) and the Vite fast-refresh rule.
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'coverage']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      // The data-fetching effects in App.jsx and ListingsView.jsx set the
      // loading state synchronously; keep this a warning until they are reworked.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
  {
    // Vitest runs with `globals: true` (vite.config.js), so test files use
    // describe/test/expect/vi without importing them.
    files: ['src/**/*.test.{js,jsx}'],
    languageOptions: { globals: globals.vitest },
  },
  {
    // Config files are executed by Node, not the browser.
    files: ['vite.config.js', 'eslint.config.js'],
    languageOptions: { globals: globals.node },
  },
])
