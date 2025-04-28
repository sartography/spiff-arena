# Spec: Process Instances - can display logs

**Test source:** `cypress/e2e/process_instances.cy.js`, test `it('can display logs', ... )`

## Summary
This test ensures that the logs for a process instance are available and correctly paginated. It runs a process, goes to the logs/events, and checks contents and pagination for the instance event log.

## Dependencies
- Custom commands: `cy.login()`, `cy.logout()`, `cy.runPrimaryBpmnFile()`, `cy.getBySel()`, `cy.basicPaginationTest()`

## Steps
1. Log in.
2. Run the primary BPMN file to ensure an instance exists.
3. Navigate to process instance list.
4. Open the first instance's details.
5. Go to the 'Events' tab.
6. Confirm presence of key log/event outputs (e.g., 'process_model_one', 'task_completed').
7. Run `cy.basicPaginationTest` using pagination options for events.

## Command Implementation Example (`cypress/support/commands.js`):

See previous spec for `basicPaginationTest` source.

## Original Test Block
```
it('can display logs', () => {
  cy.runPrimaryBpmnFile();
  cy.getBySel('process-instance-list-link').click();
  cy.getBySel('process-instance-show-link-id').first().click();
  cy.contains('Events').click();
  cy.contains('process_model_one');
  cy.contains('task_completed');
  cy.basicPaginationTest(undefined, 'pagination-options-events');
});
```
