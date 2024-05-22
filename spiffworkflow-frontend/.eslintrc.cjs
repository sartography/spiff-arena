module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'plugin:react/recommended',
    'airbnb',
    'plugin:prettier/recommended',
    'plugin:sonarjs/recommended-legacy',
    'plugin:import/errors',
    'plugin:import/warnings',
    'plugin:import/typescript',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react', 'sonarjs', '@typescript-eslint', 'unused-imports'],
  rules: {
    // according to https://github.com/typescript-eslint/typescript-eslint/issues/2621, You should turn off the eslint core rule and turn on the typescript-eslint rule
    // but not sure which of the above "extends" statements is maybe bringing in eslint core
    'max-len': ['error', { code: 200, ignoreUrls: true }],
    'no-shadow': 'off',
    '@typescript-eslint/no-shadow': ['error'],
    'jest/expect-expect': 'off',
    'react/jsx-no-bind': 'off',
    'jsx-a11y/no-autofocus': 'off',
    'jsx-a11y/label-has-associated-control': 'off',
    'no-console': 'off',
    'react/jsx-filename-extension': [
      'warn',
      { extensions: ['.js', '.jsx', '.tsx', '.ts'] },
    ],
    'react/react-in-jsx-scope': 'off',
    'react/require-default-props': 'off',
    'import/prefer-default-export': 'off',
    'no-unused-vars': 'off',
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': [
      'warn',
      {
        vars: 'all',
        varsIgnorePattern: '^_',
        args: 'after-used',
        argsIgnorePattern: '^_',
      },
    ],
    '@typescript-eslint/no-unused-vars': [
      'error',
      {
        destructuredArrayIgnorePattern: '^_',
        varsIgnorePattern: '_',
        argsIgnorePattern: '^_',
      },
    ],
    'import/extensions': [
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
};
