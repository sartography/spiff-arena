# Spec: Process Groups - can perform crud operations

**Test source:** `cypress/e2e/process_groups.cy.js`, test `it('can perform crud operations', ... )`

## Summary
This test verifies that a user can create, update, and delete a process group. It covers the UI steps from creation, validation, editing, and deletion, confirming UI and data updates after each operation.

## Dependencies
- Uses custom Cypress commands from `cypress/support/commands.js` (see below for referenced source)
    - `cy.login()`
    - `cy.logout()`
    - `cy.getBySel()`
    - `cy.createGroup()`

## Steps
1. **Authentication:** Log in before each test; log out afterward.
2. **Group creation:**
    - Generate a UUID to create a unique group name/id.
    - Use the custom `cy.createGroup(groupId, groupDisplayName)` command.
3. **Validation:** Ensure the group appears in the group list, can be clicked, and loads the correct detail page.
4. **Edit:**
    - Click the edit button (by testid 'edit-process-group-button').
    - Clear and re-enter a new display name.
    - Submit and validate the new display name updates in the UI.
5. **Delete:**
    - Click the delete button, confirm the dialog.
    - Ensure the group no longer exists in the list.
    - Confirm the process group list page loads (testid 'process-groups-loaded').
6. **Sign out:** Ensured indirectly (after test completion).

## Key Code
### Custom Commands from `cypress/support/commands.js`

```
Cypress.Commands.add('getBySel', (selector, ...args) => {
  return cy.get(`[data-testid=${selector}]`, ...args);
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
  cy.get('.user-profile-toggletip-button').click();
  cy.getBySel('logout-button').click();
  if (Cypress.env('SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK') === true) {
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
```

### Main Test Flow

```
describe('process-groups', ... ) {
  beforeEach(() => { cy.login(); });
  afterEach(() => { cy.logout(); });

  it('can perform crud operations', () => {
    const uuid = () => Cypress._.random(0, 1e6);
    const id = uuid();
    const groupDisplayName = `Test Group 1 ${id}`;
    const newGroupDisplayName = `${groupDisplayName} edited`;
    const groupId = `test-group-1-${id}`;
    cy.createGroup(groupId, groupDisplayName);

    cy.contains('Process Groups').click();
    cy.contains(groupDisplayName).click();
    cy.url().should('include', `process-groups/${groupId}`);
    cy.contains(`Process Group: ${groupDisplayName}`);

    cy.getBySel('edit-process-group-button').click();
    cy.wait(1000);
    cy.getBySel('process-group-display-name-input').clear();
    cy.getBySel('process-group-display-name-input').type(newGroupDisplayName);
    cy.contains('Submit').click();
    cy.contains(`Process Group: ${newGroupDisplayName}`);

    cy.getBySel('delete-process-group-button').click();
    cy.contains('Are you sure');
    cy.getBySel('delete-process-group-button-modal-confirmation-dialog')
      .find('.cds--btn--danger').click();
    cy.url().should('include', `process-groups`);
    cy.contains(newGroupDisplayName).should('not.exist');
    cy.getBySel('process-groups-loaded').should('exist');
  });
}
```
