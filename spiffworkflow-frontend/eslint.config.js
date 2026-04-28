import { FlatCompat } from '@eslint/eslintrc';
import { fixupConfigRules } from '@eslint/compat';
import path from 'path';
import { fileURLToPath } from 'url';
import tseslint from 'typescript-eslint';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
  resolvePluginsRelativeTo: __dirname,
});

export default tseslint.config(
  ...fixupConfigRules(compat.config({
    settings: {
      react: {
        createClass: 'createReactClass', // Regex for Component Factory to use,
        pragma: 'React', // Pragma to use, default to "React"
        fragment: 'Fragment', // Fragment to use (may be a property of <pragma>), default to "Fragment"
        version: 'detect', // React version. "detect" automatically picks the version you have installed.
        defaultVersion: '', // Default React version to use when the version you have installed cannot be detected.
        flowVersion: '0.53', // Flow version
      },
    },
    env: {
      browser: true,
      es2021: true,
    },
    ignorePatterns: ['src/rjsf/carbon_theme/**/*'],
    extends: [
      'plugin:import-x/errors',
      'plugin:import-x/typescript',
      'plugin:import-x/warnings',
      'plugin:prettier/recommended',
      'plugin:react-hooks/recommended',
      'plugin:react/recommended',
      'plugin:sonarjs/recommended-legacy',
    ],
    parser: '@typescript-eslint/parser',
    parserOptions: {
      ecmaFeatures: {
        jsx: true,
      },
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    plugins: ['@typescript-eslint', 'react', 'react-hooks', 'sonarjs'],
    rules: {
      // according to https://github.com/typescript-eslint/typescript-eslint/issues/2621, You should turn off the eslint core rule and turn on the typescript-eslint rule
      // but not sure which of the above "extends" statements is maybe bringing in eslint core
      'max-len': ['error', { code: 200, ignoreUrls: true }],
      'no-shadow': 'off',
      '@typescript-eslint/no-shadow': ['error'],
      'jest/expect-expect': 'off',
      'react/jsx-no-bind': 'off',
      'react-hooks/config': 'off',
      'react-hooks/error-boundaries': 'off',
      'react-hooks/gating': 'off',
      'react-hooks/globals': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/incompatible-library': 'off',
      'react-hooks/preserve-manual-memoization': 'off',
      'react-hooks/purity': 'off',
      'react-hooks/refs': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/set-state-in-render': 'off',
      'react-hooks/static-components': 'off',
      'react-hooks/unsupported-syntax': 'off',
      'react-hooks/use-memo': 'off',
      // FIXME: turn this back on someday
      'react/jsx-key': 'off',
      'jsx-a11y/no-autofocus': 'off',
      'jsx-a11y/label-has-associated-control': 'off',
      'no-console': 'off',
      'react/jsx-filename-extension': [
        'warn',
        { extensions: ['.js', '.jsx', '.tsx', '.ts'] },
      ],
      'react/react-in-jsx-scope': 'off',
      'react/require-default-props': 'off',
      'import-x/prefer-default-export': 'off',
      'no-unused-vars': 'off',
      'sonarjs/cognitive-complexity': 'off',
      'sonarjs/fixme-tag': 'off',
      'sonarjs/jsx-key': 'off',
      'sonarjs/no-commented-code': 'off',
      'sonarjs/no-duplicate-string': ['error', { threshold: 7 }],
      'sonarjs/no-ignored-exceptions': 'off',
      'sonarjs/no-nested-conditional': 'off',
      'sonarjs/no-nested-functions': 'off',
      'sonarjs/no-unused-vars': 'off',
      'sonarjs/pseudo-random': 'off',
      'sonarjs/regex-complexity': 'off',
      'sonarjs/slow-regex': 'off',
      'sonarjs/todo-tag': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          args: 'all',
          argsIgnorePattern: '^_',
          caughtErrors: 'all',
          caughtErrorsIgnorePattern: '(^_|^e$)',
          destructuredArrayIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          ignoreRestSiblings: true,
        },
      ],
      'import-x/extensions': [
        'error',
        'ignorePackages',
        {
          js: 'never',
          jsx: 'never',
          ts: 'never',
          tsx: 'never',
        },
      ],
      curly: ['error', 'all'],
    },
    overrides: [
      {
        files: ['**/*.test.ts', '**/*.test.tsx'],
        env: {
          jest: true,
        },
      },
    ],
  })),
);
