# Spec: Public Tasks - can start process from message form

**Test source:** `cypress/e2e/tasks.cy.js`, test `it('can start process from message form', ... )` in 'public_tasks' describe block

## Summary
Tests that a process can be started (as a public/unauthenticated user) from a public form, proceeds through required form submissions, and delivers completion feedback.

## Steps
1. Log in and out to ensure permissions are correctly reset.
2. Navigate to the public URL for 'bounty_start_multiple_forms'.
3. Enter first name, submit.
4. Enter last name, submit.
5. Confirm the completion message is shown with combined name.

## Code Reference
From `cypress/e2e/tasks.cy.js`:
```
it('can start process from message form', () => {
  cy.login();
  cy.logout();
  cy.visit('public/misc:bounty_start_multiple_forms');
  cy.get('#root_firstName').type('MyFirstName');
  cy.contains('Submit').click();
  cy.get('#root_lastName').type('MyLastName');
  cy.contains('Submit').click();
  cy.contains('We hear you. Your name is MyFirstName MyLastName.');
});
```
