# Spec: Process Instances - can paginate items

**Test source:** `cypress/e2e/process_instances.cy.js`, test `it('can paginate items', ... )`

## Summary
This test validates that pagination works for process instances by creating several instances and verifying that the pagination controls update and display correct data on different pages.

## Dependencies
- Relies on Cypress custom commands:
  - `cy.login()`
  - `cy.logout()`
  - `cy.runPrimaryBpmnFile()`
  - `cy.getBySel()`
  - `cy.basicPaginationTest()`

## Steps
1. Log in.
2. Navigate to the process model and run the primary BPMN file 5 times to ensure multiple process instances exist.
3. Click to open the process instance list (testid: 'process-instance-list-link').
4. Execute the built-in `cy.basicPaginationTest()` to validate forward/backward paging.
5. Logout (cleanup).

## Key Custom Command Implementations (from `cypress/support/commands.js`)

```
Cypress.Commands.add('basicPaginationTest',
  (
    dataTestidTagToUseToEnsureTableHasLoaded = 'paginated-entity-id',
    paginationOptionsDataTestid = 'pagination-options',
  ) => {
    cy.getBySel(paginationOptionsDataTestid).scrollIntoView();
    cy.getBySel(paginationOptionsDataTestid)
      .find('.cds--select__item-count')
      .find('.cds--select-input')
      .select('2');

    cy.contains(/\b12 of \d+/);
    cy.getBySel(dataTestidTagToUseToEnsureTableHasLoaded)
      .first()
      .then(($element) => {
        const oldId = $element.text().trim();
        cy.getBySel(paginationOptionsDataTestid)
          .find('.cds--pagination__button--forward')
          .click();
        cy.getBySel(paginationOptionsDataTestid)
          .contains(`[data-testid=${dataTestidTagToUseToEnsureTableHasLoaded}]`, oldId)
          .should('not.exist');
        cy.getBySel(paginationOptionsDataTestid).contains(/\b34 of \d+/);
        cy.getBySel(paginationOptionsDataTestid)
          .find('.cds--pagination__button--backward')
          .click();
        cy.getBySel(paginationOptionsDataTestid).contains(/\b12 of \d+/);
        cy.contains(`[data-testid=${dataTestidTagToUseToEnsureTableHasLoaded}]`, oldId);
      });
  });
```

## See Also
- Full test logic: `cypress/e2e/process_instances.cy.js`
- Command implementation: `cypress/support/commands.js`
