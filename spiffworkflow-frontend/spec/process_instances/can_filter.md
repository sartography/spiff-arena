# Spec: Process Instances - can filter

**Test source:** `cypress/e2e/process_instances.cy.js`, test `it('can filter', ... )`

## Summary
This test checks that users can filter process instances by status and date, and that the UI and filtered results behave correctly.

## Dependencies
- Custom commands (see `cypress/support/commands.js`):
    - `cy.login()`, `cy.logout()`, `cy.getBySel()`, `cy.assertAtLeastOneItemInPaginatedResults()`, `cy.assertNoItemInPaginatedResults()`
- In-test consts: `PROCESS_STATUSES`, `titleizeString`, and helper: `filterByDate()` (see below)

## Steps
1. **Navigate:** Visit `/process-instances/all` and ensure the page loads.
2. **Initial State:** Confirm at least one item is in the paginated results.
3. **Expand Filters:** Click to expand filter section (`data-testid=filter-section-expand-toggle`).
4. **Filter by Status:**
    - For each process status except 'all' and 'waiting', select a filter in the status dropdown; confirm the list updates and a status tag appears.
    - Clear status filter every time.
5. **Filter by Date:**
    - Filter by a recent past date and expect some results.
    - Filter by a future date (26h ahead) and expect no results.

## Helper Functions (inline):
```
const filterByDate = (fromDate) => {
  cy.get('#date-picker-start-from').clear();
  cy.get('#date-picker-start-from').type(format(fromDate, DATE_FORMAT));
  cy.contains('Start date to').click();

  cy.get('#time-picker-start-from').clear();
  cy.get('#time-picker-start-from').type(format(fromDate, 'HH:mm'));

  cy.get('#date-picker-end-from').clear();
  cy.get('#date-picker-end-from').type(format(fromDate, DATE_FORMAT));
  cy.contains('End date to').click();
  cy.get('#time-picker-end-from').clear();
  cy.get('#time-picker-end-from').type(format(fromDate, 'HH:mm'));
};
```

## Key Custom Commands (`cypress/support/commands.js`)
```
Cypress.Commands.add('assertAtLeastOneItemInPaginatedResults', () => {
  cy.contains(/\b[1-9]\d*[1-9]\d* of [1-9]\d*/);
});
Cypress.Commands.add('assertNoItemInPaginatedResults', () => {
  cy.contains(/\b00 of 0 items/);
});
```

## Original Test Block
Too long for inclusion—see test file for detail.
