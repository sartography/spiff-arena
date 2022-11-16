/* eslint-disable */
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  projectId: 'crax1q',
  chromeWebSecurity: false,
  e2e: {
    baseUrl: 'http://localhost:7001',
    setupNodeEvents(_on, config) {
      require('@cypress/grep/src/plugin')(config);
      return config;
    },
  },

  // this scrolls away from the elements for some reason with carbon when set to top
  // https://github.com/cypress-io/cypress/issues/2353
  // https://docs.cypress.io/guides/core-concepts/interacting-with-elements#Scrolling
  scrollBehavior: "center",
});
