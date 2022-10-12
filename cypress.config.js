/* eslint-disable */
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  projectId: 'crax1q',
  chromeWebSecurity: false,
  e2e: {
    baseUrl: 'http://localhost:7001',
    setupNodeEvents(_on, _config) {
      // implement node event listeners here
    },
  },
});
