// StrykerJS mutation testing (`npm run test:mutation`, see README).
// Stryker rewrites the files in `mutate` with every mutant switchable, copies
// the project into .stryker-tmp/ and runs the Vitest suite from vite.config.js
// once per mutant (only the tests that cover it: perTest coverage analysis).
// The HTML report lands in reports/mutation/mutation.html. The mutated surface
// mirrors the coverage include/exclude in vite.config.js.

/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  testRunner: 'vitest',
  vitest: { configFile: 'vite.config.js' },
  mutate: ['src/**/*.{js,jsx}', '!src/**/*.test.{js,jsx}', '!src/main.jsx'],
  coverageAnalysis: 'perTest',
  reporters: ['clear-text', 'progress', 'html'],
  // `break` is a floor just under the current total score (mutants in files
  // without unit tests count as survived), so CI catches regressions; raise it
  // as survivors get killed. high/low only colour the report.
  thresholds: { high: 80, low: 60, break: 30 },
}
