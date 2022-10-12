'use strict';

const coverage = process.env.COVERAGE;
const path = require('path');
const {
  DefinePlugin,
  NormalModuleReplacementPlugin
} = require('webpack');
const basePath = '.';
const absoluteBasePath = path.resolve(path.join(__dirname, basePath));

module.exports = function(karma) {
  karma.set({

    frameworks: [
      'webpack',
      'mocha',
      'sinon-chai'
    ],

    files: [
      'test/spec/**/*Spec.js',
    ],

    reporters: [ 'dots' ],

    preprocessors: {
      'test/spec/**/*Spec.js': [ 'webpack', 'env' ]
    },

    browsers: [ 'ChromeHeadless' ],

    browserNoActivityTimeout: 30000,

    singleRun: true,
    autoWatch: false,

    webpack: {
      mode: 'development',
      module: {
        rules: [
          {
            test: /\.(css|bpmn)$/,
            use: 'raw-loader'
          },
          {
            test: /\.m?js$/,
            exclude: /node_modules/,
            use: {
              loader: 'babel-loader',
              options: {
                plugins: [
                  [ '@babel/plugin-transform-react-jsx', {
                    'importSource': '@bpmn-io/properties-panel/preact',
                    'runtime': 'automatic'
                  } ]
                ]
              }
            }
          },
          {
            test: /\.svg$/,
            use: [ 'react-svg-loader' ]
          }
        ].concat(coverage ?
          {
            test: /\.js$/,
            use: {
              loader: 'istanbul-instrumenter-loader',
              options: { esModules: true }
            },
            enforce: 'post',
            include: /src\.*/,
            exclude: /node_modules/
          } : []
        )
      },
      plugins: [
        new DefinePlugin({
          // @barmac: process.env has to be defined to make @testing-library/preact work
          'process.env': {}
        }),
        new NormalModuleReplacementPlugin(
          /^preact(\/[^/]+)?$/,
          function(resource) {

            const replMap = {
              'preact/hooks': path.resolve('node_modules/@bpmn-io/properties-panel/preact/hooks/dist/hooks.module.js'),
              'preact/jsx-runtime': path.resolve('node_modules/@bpmn-io/properties-panel/preact/jsx-runtime/dist/jsxRuntime.module.js'),
              'preact': path.resolve('node_modules/@bpmn-io/properties-panel/preact/dist/preact.module.js')
            };

            const replacement = replMap[resource.request];

            if (!replacement) {
              return;
            }

            resource.request = replacement;
          }
        ),
        new NormalModuleReplacementPlugin(
          /^preact\/hooks/,
          path.resolve('node_modules/@bpmn-io/properties-panel/preact/hooks/dist/hooks.module.js')
        )
      ],
      resolve: {
        mainFields: [
          'browser',
          'module',
          'main'
        ],
        alias: {
          'preact': '@bpmn-io/properties-panel/preact',
          'react': '@bpmn-io/properties-panel/preact/compat',
          'react-dom': '@bpmn-io/properties-panel/preact/compat'
        },
        modules: [
          'node_modules',
          absoluteBasePath
        ]
      },
      devtool: 'eval-source-map'
    }
  });
};
