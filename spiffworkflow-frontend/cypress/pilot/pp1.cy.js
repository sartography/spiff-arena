const approveWithUser = (
  username,
  processInstanceId,
  expectAdditionalApprovalInfoPage = false
) => {
  cy.login(username, username);
  cy.visit('/admin/process-instances/find-by-id');
  cy.get('#process-instance-id-input').type(processInstanceId);
  cy.get('button')
    .contains(/^Submit$/)
    .click();

  cy.contains('Tasks I can complete', { timeout: 30000 });
  cy.get('.cds--btn').contains(/^Go$/).click();

  // approve!
  cy.get('#root-app').click();
  cy.get('button')
    .contains(/^Submit$/)
    .click();
  if (expectAdditionalApprovalInfoPage) {
    cy.contains(expectAdditionalApprovalInfoPage, { timeout: 30000 });
    cy.get('button')
      .contains(/^Continue$/)
      .click();
  }
  cy.location({ timeout: 30000 }).should((loc) => {
    expect(loc.pathname).to.eq('/tasks');
  });
  cy.logout();
};

describe('pp1', () => {
  it('can run PP1', () => {
    cy.login('core-a1.contributor', 'core-a1.contributor');
    cy.visit('/');
    cy.contains('Start New +').click();
    cy.contains('Raise New Demand Request');
    cy.runPrimaryBpmnFile(true);
    cy.contains('Please select the type of request to start the process.');
    // wait a second to ensure we can click the radio button
    cy.wait(1000);
    cy.get('input#root-procurement').click();
    cy.wait(1000);
    cy.get('button')
      .contains(/^Submit$/)
      .click();
    cy.contains(
      'Submit a new demand request for the procurement of needed items',
      { timeout: 30000 }
    );

    cy.url().then((currentUrl) => {
      // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
      // extract the digits after /tasks
      const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];

      cy.get('#root_project').select('18564');
      cy.get('#root_category').select('soft_and_lic');
      cy.get('#root_purpose').clear().type('need the software for my work');
      cy.get('#root_criticality').select('High');
      cy.get('#root_period').clear().type('2023-10-10');
      cy.get('#root_vendor').clear().type('sartography');
      cy.get('#root_payment_method').select('Bank Transfer');
      cy.get('#root_project').select('18564');
      cy.get('#root_category').select('soft_and_lic');
      cy.get('button')
        .contains(/^Submit$/)
        .click();

      cy.contains('Task: Enter NDR Items', { timeout: 30000 });
      cy.get('#root_0_sub_category').select('op_src');
      cy.get('#root_0_item').clear().type('spiffworkflow');
      cy.get('#root_0_qty').clear().type('1');
      cy.get('#root_0_currency_type').select('Fiat');
      cy.get('#root_0_currency').select('AUD');
      cy.get('#root_0_unit_price').type('100');
      cy.get('button')
        .contains(/^Submit$/)
        .click();

      cy.contains(
        'Review and provide any supporting information or files for your request.',
        { timeout: 30000 }
      );
      cy.contains('Submit the Request').click();
      cy.get('input[value="Submit the Request"]').click();
      cy.get('button')
        .contains(/^Submit$/)
        .click();
      cy.contains('Tasks for my open instances', { timeout: 30000 });

      cy.logout();
      approveWithUser(
        'infra.project-lead',
        processInstanceId,
        'Task: Reminder: Request Additional Budget'
      );
      approveWithUser('ppg.ba-a1.sme', processInstanceId);
      approveWithUser('security-a1.sme', processInstanceId);
      approveWithUser(
        'infra-a1.sme',
        processInstanceId,
        'Task: Update Application Landscape'
      );
      approveWithUser('legal-a1.sme', processInstanceId);
    });
  });
});
