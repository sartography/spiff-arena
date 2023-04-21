module.exports = {
  module: {
    rules: [
      {
        test: /\.m?[jt]sx?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            plugins: [
              [
                '@babel/plugin-transform-react-jsx',
                {
                  pragma: 'h',
                  pragmaFrag: 'Fragment',
                },
              ],
              '@babel/preset-react',
              '@babel/plugin-transform-typescript',
              {
                importSource: '@bpmn-io/properties-panel/preact',
                runtime: 'automatic',
              },
              '@babel/plugin-proposal-class-properties',
              { loose: true },
              '@babel/plugin-proposal-private-methods',
              { loose: true },
              '@babel/plugin-proposal-private-property-in-object',
              { loose: true },
            ],
          },
        },
      },
    ],
  },
  webpack: {
    configure: {
      resolve: {
        alias: {
          inferno:
            process.env.NODE_ENV !== 'production'
              ? 'inferno/dist/index.dev.esm.js'
              : 'inferno/dist/index.esm.js',
          react: 'preact/compat',
          'react-dom/test-utils': 'preact/test-utils',
          'react-dom': 'preact/compat', // Must be below test-utils
          'react/jsx-runtime': 'preact/jsx-runtime',
        },
      },
    },
  },
  babel: {
    presets: [
      '@babel/preset-env',
      ['@babel/preset-react', { runtime: 'automatic' }],
      '@babel/preset-typescript',
    ],
    // plugins: [],
    loaderOptions: (babelLoaderOptions) => {
      return babelLoaderOptions;
    },
  },
};
