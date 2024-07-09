import { modifyProcessIdentifierForPathParam } from '../../src/helpers';
import { miscDisplayName } from './helpers';
import 'cypress-file-upload';

// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add('getBySel', (selector, ...args) => {
  return cy.get(`[data-qa=${selector}]`, ...args);
});

Cypress.Commands.add('navigateToHome', () => {
  cy.getBySel('header-menu-expand-button').click();
  cy.getBySel('side-nav-items').contains('Home').click();
});

Cypress.Commands.add('navigateToAdmin', () => {
  cy.visit('/process-groups');
});

Cypress.Commands.add('login', (username, password) => {
  cy.visit('/process-groups');
  let usernameToUse = username;
  let passwordToUse = password;
  if (!usernameToUse) {
    usernameToUse =
      Cypress.env('SPIFFWORKFLOW_FRONTEND_USERNAME') || 'ciadmin1';
    passwordToUse =
      Cypress.env('SPIFFWORKFLOW_FRONTEND_PASSWORD') || 'ciadmin1';
  }
  cy.get('#username').type(usernameToUse);
  cy.get('#password').type(passwordToUse);
  if (Cypress.env('SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK') === true) {
    cy.get('#kc-login').click();
  } else {
    cy.get('#spiff-login-button').click();
  }
});

Cypress.Commands.add('logout', (_selector, ..._args) => {
  cy.wait(2000);
  // click the profile thingy in the top right
  cy.get('.user-profile-toggletip-button').click();

  cy.getBySel('logout-button').click();
  if (Cypress.env('SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK') === true) {
    // otherwise we can click logout, quickly load the next page, and the javascript
    // doesn't have time to actually sign you out
    // cy.wait(4000);
    cy.contains('Sign in to your account');
  } else {
    cy.get('#spiff-login-button').should('exist');
  }
});

Cypress.Commands.add('createGroup', (groupId, groupDisplayName) => {
  cy.contains(groupId).should('not.exist');
  cy.contains('Add a process group').click();
  cy.get('input[name=display_name]').type(groupDisplayName);
  cy.get('input[name=display_name]').should('have.value', groupDisplayName);
  cy.get('input[name=id]').should('have.value', groupId);
  cy.contains('Submit').click();

  cy.url().should('include', `process-groups/${groupId}`);
  cy.contains(`Process Group: ${groupDisplayName}`);
});

Cypress.Commands.add('createModel', (groupId, modelId, modelDisplayName) => {
  cy.contains(modelId).should('not.exist');

  const dasherizedGroupId = groupId.replace(/\//g, '-');
  cy.getBySel(`add-process-model-for-group-${dasherizedGroupId}`).click();
  cy.get('input[name=display_name]').type(modelDisplayName);
  cy.get('input[name=display_name]').should('have.value', modelDisplayName);
  cy.get('input[name=id]').should('have.value', modelId);
  cy.contains('Submit').click();

  cy.url().should(
    'include',
    `process-models/${modifyProcessIdentifierForPathParam(groupId)}:${modelId}`,
  );
  cy.contains(`Process Model: ${modelDisplayName}`);
});

// Intended to be run from the process model show page
Cypress.Commands.add(
  'runPrimaryBpmnFile',
  (
    expectAutoRedirectToHumanTask = false,
    returnToProcessModelShow = true,
    processInstanceExpectedToBeComplete = true,
  ) => {
    cy.getBySel('start-process-instance').click();
    if (expectAutoRedirectToHumanTask) {
      // the url changes immediately, so also make sure we get some content from the next page, "Task:",
      // or else when we try to interact with the page, it'll re-render and we'll get an error with cypress.
      cy.url().should('include', `/tasks/`);
      cy.contains('Task: ', { timeout: 30000 });
    } else {
      cy.url().should('include', `/process-instances`);
      cy.contains('Process Instance Id');
      if (processInstanceExpectedToBeComplete) {
        cy.contains('complete');
      }
      if (returnToProcessModelShow) {
        cy.getBySel('process-model-breadcrumb-link').click();
        cy.getBySel('process-model-show-permissions-loaded').should('exist');
      }
    }
  },
);

Cypress.Commands.add(
  'navigateToProcessModel',
  (groupDisplayName, modelDisplayName) => {
    cy.navigateToAdmin();
    cy.contains(miscDisplayName).click();
    cy.contains(`Process Group: ${miscDisplayName}`, { timeout: 10000 });
    cy.contains(groupDisplayName).click();
    cy.contains(`Process Group: ${groupDisplayName}`);
    // https://stackoverflow.com/q/51254946/6090676
    cy.getBySel('process-model-show-link').contains(modelDisplayName).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
  },
);

Cypress.Commands.add(
  'basicPaginationTest',
  (
    dataQaTagToUseToEnsureTableHasLoaded = 'paginated-entity-id',
    paginationOptionsDataQa = 'pagination-options',
  ) => {
    cy.getBySel(paginationOptionsDataQa).scrollIntoView();
    cy.getBySel(paginationOptionsDataQa)
      .find('.cds--select__item-count')
      .find('.cds--select-input')
      .select('2');

    // NOTE: this is a em dash instead of en dash
    cy.contains(/\b1–2 of \d+/);

    // ok, trying to ensure that we have everything loaded before we leave this
    // function and try to sign out. Just showing results 1-2 of blah is not good enough,
    // since the ajax request may not have finished yet.
    // to be sure it's finished, grab the log id from page 1. remember it.
    // then use the magical contains command that waits for the element to exist AND
    // for that element to contain the text we're looking for.
    cy.getBySel(dataQaTagToUseToEnsureTableHasLoaded)
      .first()
      .then(($element) => {
        const oldId = $element.text().trim();
        cy.getBySel(paginationOptionsDataQa)
          .find('.cds--pagination__button--forward')
          .click();
        cy.getBySel(paginationOptionsDataQa)
          .contains(`[data-qa=${dataQaTagToUseToEnsureTableHasLoaded}]`, oldId)
          .should('not.exist');
        cy.getBySel(paginationOptionsDataQa).contains(/\b3–4 of \d+/);
        cy.getBySel(paginationOptionsDataQa)
          .find('.cds--pagination__button--backward')
          .click();
        cy.getBySel(paginationOptionsDataQa).contains(/\b1–2 of \d+/);
        cy.contains(`[data-qa=${dataQaTagToUseToEnsureTableHasLoaded}]`, oldId);
      });
  },
);

Cypress.Commands.add('assertAtLeastOneItemInPaginatedResults', () => {
  cy.contains(/\b[1-9]\d*–[1-9]\d* of [1-9]\d*/);
});

Cypress.Commands.add('assertNoItemInPaginatedResults', () => {
  cy.contains(/\b0–0 of 0 items/);
});

Cypress.Commands.add('deleteProcessModelAndConfirm', (buttonId, groupId) => {
  cy.getBySel(buttonId).click();
  cy.contains('Are you sure');
  cy.getBySel('delete-process-model-button-modal-confirmation-dialog')
    .find('.cds--btn--danger')
    .click();
  cy.url().should(
    'include',
    `process-groups/${modifyProcessIdentifierForPathParam(groupId)}`,
  );
});
