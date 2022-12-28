describe('process-groups', () => {
  beforeEach(() => {
    cy.login();
  });
  afterEach(() => {
    cy.logout();
  });

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
    cy.get('input[name=display_name]').clear().type(newGroupDisplayName);
    cy.contains('Submit').click();
    cy.contains(`Process Group: ${newGroupDisplayName}`);

    cy.getBySel('delete-process-group-button').click();
    cy.contains('Are you sure');
    cy.getBySel('delete-process-group-button-modal-confirmation-dialog')
      .find('.cds--btn--danger')
      .click();
    cy.url().should('include', `process-groups`);
    cy.contains(newGroupDisplayName).should('not.exist');

    // meaning the process group list page is loaded, so we can sign out safely without worrying about ajax requests failing
    cy.get('.tile-process-group-content-container').should('exist');
  });

  // process groups no longer has pagination post-tiles
  // it('can paginate items', () => {
  //   cy.basicPaginationTest();
  // });
});
