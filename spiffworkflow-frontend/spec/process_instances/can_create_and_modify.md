# Spec: Process Instances - can create a new instance and can modify

**Test source:** `cypress/e2e/process_instances.cy.js`, test `it('can create a new instance and can modify', ... )`

## Summary
This test verifies that a user can create a new process instance and make modifications to DMN and BPMN files, triggering changes in process execution as expected.

## Dependencies
- Custom Cypress commands (see key code below):
    - `cy.login()`, `cy.logout()`, `cy.navigateToProcessModel()`, `cy.runPrimaryBpmnFile()`
    - `cy.getBySel()`
- In-test functions:
    - `updateDmnText()`
    - `updateBpmnPythonScript()`
- Test constants and values sourced from process model structure.

## Steps
1. **Setup and Navigation:**
    - Log in.
    - Navigate to process model 'Acceptance Tests Group One' -> 'Acceptance Tests Model 1'.
2. **Initial State Validation:**
    - Assert the original DMN output does NOT exist.
3. **Run initial BPMN file.**
4. **Modify DMN file:**
    - Edit 'awesome_decision.dmn' to replace text in the decision table.
    - Save, return to process model, and run BPMN file.
5. **Restore DMN to original:**
    - Repeat edit to set DMN output text back.
    - Save and rerun BPMN file.
6. **Modify BPMN Python script:**
    - Edit 'process_model_one.bpmn' to alter embedded python logic.
    - Save and rerun BPMN file.
7. **Restore BPMN python script to original:**
    - Edit and restore python script.
    - Save and rerun BPMN file.
8. **Cleanup/logout:**
    - Performed in `afterEach`.

## Helper Functions (in-file)
```
const updateDmnText = (oldText, newText, elementId = 'wonderful_process') => {
  cy.get(`g[data-element-id=${elementId}]`).click();
  cy.get('.dmn-icon-decision-table').click();
  const item = cy.contains(oldText);
  item.clear();
  cy.contains('Process Model File:').click();
  item.type(`"${newText}"`);
  cy.wait(500);
  cy.getBySel('process-model-file-save-button').click();
};

const updateBpmnPythonScript = (pythonScript, elementId = 'process_script') => {
  cy.get(`g[data-element-id=${elementId}]`).click();
  cy.contains(/^Script$/).click();
  cy.get('textarea[name="pythonScript_bpmn:script"]').clear();
  cy.get('textarea[name="pythonScript_bpmn:script"]').type(pythonScript);
  cy.wait(500);
  cy.getBySel('process-model-file-save-button').click();
};
```

## Key Custom Commands (from `cypress/support/commands.js`)
See prior spec for login/logout and `getBySel`. Additionally:
```
Cypress.Commands.add(
  'navigateToProcessModel',
  (groupDisplayName, modelDisplayName) => {
    cy.navigateToAdmin();
    cy.contains(miscDisplayName).click();
    cy.contains(`Process Group: ${miscDisplayName}`, { timeout: 10000 });
    cy.contains(groupDisplayName).click();
    cy.contains(`Process Group: ${groupDisplayName}`);
    cy.getBySel('process-model-show-link').contains(modelDisplayName).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
  },
);

Cypress.Commands.add(
  'runPrimaryBpmnFile',
  (
    expectAutoRedirectToHumanTask = false,
    returnToProcessModelShow = true,
    processInstanceExpectedToBeComplete = true,
  ) => {
    cy.getBySel('start-process-instance').click();
    if (expectAutoRedirectToHumanTask) {
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
  }
);
```

## Original Test Block
See `cypress/e2e/process_instances.cy.js` for full test block source. (Block too large to include here in entirety.)
