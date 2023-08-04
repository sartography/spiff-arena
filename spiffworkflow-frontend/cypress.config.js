/* eslint-disable */
const { defineConfig } = require("cypress");
const { rm } = require("fs/promises");

// yes use video compression in CI, where we will set the env var so we upload to cypress dashboard
const useVideoCompression = !!process.env.CYPRESS_RECORD_KEY;

// https://github.com/cypress-io/cypress/issues/2522
const deleteVideosOnSuccess = (on) => {
  const filesToDelete = [];
  on("after:spec", (_spec, results) => {
    if (results.stats.failures === 0 && results.video) {
      filesToDelete.push(results.video);
    }
  });
  on("after:run", async () => {
    if (filesToDelete.length) {
      console.log(
        "after:run hook: Deleting %d video(s) from successful specs",
        filesToDelete.length
      );
      await Promise.all(filesToDelete.map((videoFile) => rm(videoFile)));
    }
  });
};

let spiffWorkflowFrontendUrl = `http://localhost:${
  process.env.SPIFFWORKFLOW_FRONTEND_PORT || 7001
}`;

if (process.env.SPIFFWORKFLOW_FRONTEND_URL) {
  spiffWorkflowFrontendUrl = process.env.SPIFFWORKFLOW_FRONTEND_URL;
}

const cypressConfig = {
  projectId: "crax1q",
  defaultCommandTimeout: 20000,
  videoUploadOnPasses: false,
  chromeWebSecurity: false,
  e2e: {
    baseUrl: spiffWorkflowFrontendUrl,
    setupNodeEvents(on, config) {
      deleteVideosOnSuccess(on);
      require("@cypress/grep/src/plugin")(config);
      return config;
    },
  },

  // this scrolls away from the elements for some reason with carbon when set to top
  // https://github.com/cypress-io/cypress/issues/2353
  // https://docs.cypress.io/guides/core-concepts/interacting-with-elements#Scrolling
  scrollBehavior: "center",
};

if (!process.env.CYPRESS_RECORD_KEY) {
  // since it's slow
  cypressConfig.videoCompression = false;
}

module.exports = defineConfig(cypressConfig)
