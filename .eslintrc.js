module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'airbnb',
    'plugin:bpmn-io/es6',
    'plugin:prettier/recommended',
    'plugin:sonarjs/recommended',
    'plugin:import/errors',
    'plugin:import/warnings',
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    'jsx-a11y/no-autofocus': 'off',
    'jsx-a11y/label-has-associated-control': 'off',
    'no-console': 'off',
    'no-unused-vars': [
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

    // We could try turning these on at some point but do not want to force it now
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    'react/jsx-filename-extension': [1, { extensions: ['.js', '.jsx'] }],
    'no-use-before-define': 0,
    'func-names': 'off',
    'react/destructuring-assignment': 'off',
    'import/prefer-default-export': 'off',
    'no-restricted-syntax': 'off',
  },
};
