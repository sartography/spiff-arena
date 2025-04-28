# Spec: Public Tasks - can complete a guest task

**Test source:** `cypress/e2e/tasks.cy.js`, test `it('can complete a guest task', ... )` in 'public_tasks' block

## Summary
This test ensures that a process designed to be completed by a guest can be started, and all steps completed, as an unauthenticated user (public link), following a complex workflow. Also ensures the link becomes invalid after use.

## Steps
1. Login and start the target process ('Shared Resources' > 'task-with-guest-form'). Start (run) the primary BPMN file for the case.
2. Extract the guest task public link (from metadata field `first_task_url`).
3. Log out.
4. Visit public guest/task URL as a guest. Complete both forms by clicking submit on each, confirm completion message.
5. Check the link cannot be reused (should show error on second visit).
6. Click the public home link, sign out, and ensure redirection to sign-in page or login button (depending on auth system).

## Code Reference
From `cypress/e2e/tasks.cy.js`:
```
it('can complete a guest task', () => {
  cy.login();
  const groupDisplayName = 'Shared Resources';
  const modelDisplayName = 'task-with-guest-form';
  cy.navigateToProcessModel(groupDisplayName, modelDisplayName);
  cy.runPrimaryBpmnFile(false, false, false);
  cy.get('[data-testid="metadata-value-first_task_url"] a')
    .invoke('attr', 'href')
    .then((hrefValue) => {
      cy.logout();
      cy.visit(hrefValue);
      // form 1
      cy.contains('Submit').click();
      // form 2
      cy.contains('Submit').click();
      cy.contains('You are done. Yay!');
      cy.visit(hrefValue);
      cy.contains('Error retrieving content.');
      cy.getBySel('public-home-link').click();
      cy.getBySel('public-sign-out').click();
      if (Cypress.env('SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK') === true) {
        cy.contains('Sign in to your account');
      } else {
        cy.get('#spiff-login-button').should('exist');
      }
    });
});
```
