# Spec: Tasks - can complete and navigate a form

**Test source:** `cypress/e2e/tasks.cy.js`, test `it('can complete and navigate a form', ... )`

## Summary
Verifies that a user can complete a multi-form task by navigating through each form, entering data, and submitting until complete. Also checks follow-up details and proper status display.

## Dependencies
- Cascading custom commands and helpers (see below):
    - `cy.login()`, `cy.logout()`, `cy.getBySel()`, `cy.navigateToProcessModel()`, `cy.runPrimaryBpmnFile()`
- Local helper: `submitInputIntoFormField()`

## Steps
1. Log in.
2. Navigate to group + model.
3. Start (run) a BPMN process (with form).
4. For each form (1–4), enter data in the correct input and submit (see below for helper logic).
5. Between forms and at end, validate data and workflow status/class in UI.
6. Use home navigation and the home page's Go button to resume/continue workflow.
7. At end, verify instance status is 'complete'.

## Helper Implementation
```
const submitInputIntoFormField = (taskName, fieldKey, fieldValue, checkDraftData) => {
  cy.contains(`Task: ${taskName}`, { timeout: 10000 });
  cy.get(fieldKey).clear();
  cy.get(fieldKey).type(fieldValue);
  cy.wait(100); // debounce for input save
  if (checkDraftData) {
    cy.wait(1000);
    cy.reload();
    cy.get(fieldKey).should('have.value', fieldValue);
  }
  cy.contains('Submit').click();
};
```

## Original Test Block
Block too large for full inclusion; see `cypress/e2e/tasks.cy.js`.
