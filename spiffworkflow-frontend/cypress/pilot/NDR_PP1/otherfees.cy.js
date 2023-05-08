const submitWithUser = (
  username,
  password,
  processInstanceId,
  expectAdditionalApprovalInfoPage = false,
  approvaltype
) => {
  cy.wait(2000);
  cy.log('========Login with : ', username);
  cy.log('========processInstanceId: ', processInstanceId);
  cy.login(username, password);

  cy.wait(1000);
  cy.log('=======visit find by id : ');
  cy.visit('/admin/process-instances/find-by-id');
  cy.wait(3000);
  cy.get('#process-instance-id-input').type(processInstanceId);

  cy.get('button')
    .contains(/^Submit$/)
    .click();

  cy.wait(2000);
  cy.contains('Tasks I can complete', { timeout: 60000 });

  cy.get('.cds--btn').contains(/^Go$/).click();

  cy.wait(2000);
  // approve!
  if (approvaltype === "approve") {
    cy.get('#root > label:nth-child(1)').click();
    cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' is approving this.'));
  } else if (approvaltype === "reject") {
    cy.get('#root > label:nth-child(3)').click();
    cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' is rejecting this.'));
  } else if (approvaltype === "needmoreinfo") {
    cy.get('#root > label:nth-child(2)').click();
    cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' needs additional info. Coworking is not only about providing a physical place, but also about establishing a community. Its rapid growth has been seen as a possible way for city planners to address.'));
  } else if (approvaltype === "providemoreinfo") {
    //Form 1
    cy.contains('Task: Submit Details', { timeout: 60000 });
    cy.get('button')
      .contains(/^Submit$/)
      .click();
    //Form 2      
    /*cy.contains('Task: Enter NDR Items', { timeout: 60000 });
    cy.get('button')
      .contains(/^Submit$/)
      .click();*/
    //Form 3
    cy.contains(
      'Task: Review the Request',
      { timeout: 60000 });

    cy.get('.cds--text-area__wrapper').find('#root').clear().type('Providing additional info. Coworking tends to fall into two sides: Those that are real-estate-centric (all about selling desks and offices first) while others are community-centric (focused on building community that happens to also have offices)');

    //cy.contains('Submit the Request').click();
    //cy.get('input[value="Submit the Request"]').click();

  } else {

  }


  cy.get('button')
    .contains(/^Submit$/)
    .click();

  if (expectAdditionalApprovalInfoPage) {
    cy.contains(expectAdditionalApprovalInfoPage, { timeout: 60000 });

    cy.get('button')
      .contains(/^Continue$/)
      .click();

  }

  cy.visit('/');

  cy.location({ timeout: 60000 }).should((loc) => {
    expect(loc.pathname).to.eq('/');
  });
  cy.wait(2000);
  cy.logout();
  cy.wait(2000);
};

describe('Other Fees Path - Without Files', () => {

  Cypress._.times(1, () => {
    //Budget owner approves the request
    it('Budget owner approves', () => {
      let username = Cypress.env('requestor_username');
      let password = Cypress.env('requestor_password');
      cy.log('=====username : ' + username);
      cy.log('=====password : ' + password);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services');

      cy.runPrimaryBpmnFile(true);

      /* cy.contains('Please select the type of request to start the process.');
       // wait a second to ensure we can click the radio button
 
       cy.wait(2000);
       cy.get('input#root-procurement').click();
       cy.wait(2000);
 
 
       cy.get('button')
         .contains(/^Submit$/)
         .click();
 */

      cy.contains(
        'Request Goods or Services',
        { timeout: 60000 }
      );

       cy.wait(5000);
            cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('other_fees');
        cy.get('#root_purpose').clear().type('Other Fees and Expenses means, collectively, all fees and expenses payable to Lenders under the Loan Documents, other than principal, interest and default interest/penalty amounts.');
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('ABC CO');
        cy.get('#root_payment_method').select('Reimbursement');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
        //item 0
        cy.get('#root_item_0_sub_category').select('bounties');
        cy.get('#root_item_0_item_name').clear().type('A bounty is a payment or reward of money to locate');
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');


        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('coworking');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Crypto');
        cy.get('#root_item_1_currency').select('SNT');
        cy.get('#root_item_1_unit_price').type('1355');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

        //cy.contains('Submit the Request').click();

        //cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();


        cy.get('button')
          .contains(/^Return to Home$/)
          .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
        cy.wait(1000);

        let budgetOwnerUsername = Cypress.env('budgetowner_username');
        let budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log('=====budgetOwnerUsername : ' + budgetOwnerUsername);
        cy.log('=====budgetOwnerPassword : ' + budgetOwnerPassword);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          "approve"
        );

      });
    });

    //Budget owner rejects the request
    it('Budget owner rejects', () => {
      let username = Cypress.env('requestor_username');
      let password = Cypress.env('requestor_password');
      cy.log('=====username : ' + username);
      cy.log('=====password : ' + password);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services');

      cy.runPrimaryBpmnFile(true);

      /* cy.contains('Please select the type of request to start the process.');
       // wait a second to ensure we can click the radio button
 
       cy.wait(2000);
       cy.get('input#root-procurement').click();
       cy.wait(2000);
 
 
       cy.get('button')
         .contains(/^Submit$/)
         .click();
 */

      cy.contains(
        'Request Goods or Services',
        { timeout: 60000 }
      );

       cy.wait(5000);
            cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('other_fees');
        cy.get('#root_purpose').clear().type('Other Fees and Expenses means, collectively, all fees and expenses payable to Lenders under the Loan Documents, other than principal, interest and default interest/penalty amounts.');
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('24-02-2036');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('CO-WORK ENG');
        cy.get('#root_payment_method').select('Bank Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
        cy.get('#root_item_0_sub_category').select('coworking');
        cy.get('#root_item_0_item_name').clear().type('Coworking is an arrangement in which workers for different companies share an office space');
        cy.get('#root_item_0_qty').clear().type('5');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('EUR');
        cy.get('#root_item_0_unit_price').type('250');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

        //cy.contains('Submit the Request').click();

        //cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.get('button')
          .contains(/^Return to Home$/)
          .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
        cy.wait(1000);

        let budgetOwnerUsername = Cypress.env('budgetowner_username');
        let budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log('=====budgetOwnerUsername : ' + budgetOwnerUsername);
        cy.log('=====budgetOwnerPassword : ' + budgetOwnerPassword);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          "reject"
        );

      });
    });

    //Budget owner request for additional details
    it('Budget owner need more info', () => {
      let username = Cypress.env('requestor_username');
      let password = Cypress.env('requestor_password');
      cy.log('=====username : ' + username);
      cy.log('=====password : ' + password);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services');

      cy.runPrimaryBpmnFile(true);

      /* cy.contains('Please select the type of request to start the process.');
       // wait a second to ensure we can click the radio button
 
       cy.wait(2000);
       cy.get('input#root-procurement').click();
       cy.wait(2000);
 
 
       cy.get('button')
         .contains(/^Submit$/)
         .click();
 */

      cy.contains(
        'Request Goods or Services',
        { timeout: 60000 }
      );

       cy.wait(5000);
            cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('other_fees');
        cy.get('#root_purpose').clear().type(' It allows cost savings and convenience through the use of common infrastructures, such as equipment, utilities and receptionist and custodial services, and in some cases refreshments and parcel services.\nhttps://en.wikipedia.org/wiki/Coworking');
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('05-02-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Bounty Co');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
        cy.get('#root_item_0_sub_category').select('bounties');
        cy.get('#root_item_0_item_name').clear().type('Coworking is not only about providing a physical place, but also about establishing a community.');
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('450');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('It\’s free and easy to post a job. Simply fill in a title, description and budget and competitive bids come within minutes. No job is too big or too small. We\'ve got freelancers for jobs of any size or budget across 1800 skills. No job is too complex.');

        //cy.contains('Submit the Request').click();

        //cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.get('button')
          .contains(/^Return to Home$/)
          .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
        cy.wait(1000);

        let budgetOwnerUsername = Cypress.env('budgetowner_username');
        let budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log('=====budgetOwnerUsername : ' + budgetOwnerUsername);
        cy.log('=====budgetOwnerPassword : ' + budgetOwnerPassword);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          "needmoreinfo"
        );

        //requestor sending additional info
        submitWithUser(
          username,
          password,
          processInstanceId,
          null,
          "providemoreinfo"
        );

        //budget owner approves second time
        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          "approve"
        );

      });
    });

  });
});

describe('Other Fees Path - With Files', () => {

  Cypress._.times(1, () => {
    //Budget owner approves the request
    it('Budget owner approves', () => {
      let username = Cypress.env('requestor_username');
      let password = Cypress.env('requestor_password');
      cy.log('=====username : ' + username);
      cy.log('=====password : ' + password);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services');

      cy.runPrimaryBpmnFile(true);

      /* cy.contains('Please select the type of request to start the process.');
       // wait a second to ensure we can click the radio button
 
       cy.wait(2000);
       cy.get('input#root-procurement').click();
       cy.wait(2000);
 
 
       cy.get('button')
         .contains(/^Submit$/)
         .click();
 */

      cy.contains(
        'Request Goods or Services',
        { timeout: 60000 }
      );

       cy.wait(5000);
            cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('other_fees');
        cy.get('#root_purpose').clear().type('It allows cost savings and convenience through the use of common infrastructures, such as equipment, utilities and receptionist and custodial services, and in some cases refreshments and parcel acceptance services');
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('15-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Embassar');
        cy.get('#root_payment_method').select('Reimbursement');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
        //item 0
        cy.get('#root_item_0_sub_category').select('bounties');
        cy.get('#root_item_0_item_name').clear().type('A bounty is a payment or reward of money to locate');
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('coworking');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Crypto');
        cy.get('#root_item_1_currency').select('DAI');
        cy.get('#root_item_1_unit_price').type('4250');

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get("input[type=file]")
          .attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get("input[type=file]")
          .attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);

        cy.get("input[type=file]")
          .attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);

        cy.get("input[type=file]")
          .attachFile(['sampletext.txt']);

        cy.wait(2000);

        //cy.contains('Submit the Request').click();

        //cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(20000);
        cy.get('button')
          .contains(/^Return to Home$/)
          .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
        cy.wait(1000);

        let budgetOwnerUsername = Cypress.env('budgetowner_username');
        let budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log('=====budgetOwnerUsername : ' + budgetOwnerUsername);
        cy.log('=====budgetOwnerPassword : ' + budgetOwnerPassword);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          "approve"
        );

      });
    });

    //Budget owner rejects the request
    it('Budget owner rejects', () => {
      let username = Cypress.env('requestor_username');
      let password = Cypress.env('requestor_password');
      cy.log('=====username : ' + username);
      cy.log('=====password : ' + password);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services');

      cy.runPrimaryBpmnFile(true);

      /* cy.contains('Please select the type of request to start the process.');
       // wait a second to ensure we can click the radio button
 
       cy.wait(2000);
       cy.get('input#root-procurement').click();
       cy.wait(2000);
 
 
       cy.get('button')
         .contains(/^Submit$/)
         .click();
 */

      cy.contains(
        'Request Goods or Services',
        { timeout: 60000 }
      );

       cy.wait(5000);
            cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('other_fees');
        cy.get('#root_purpose').clear().type('Other Fees and Expenses means, collectively, all fees and expenses payable to Lenders under the Loan Documents, other than principal, interest and default interest/penalty amounts.');
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('20-02-2026');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('CO-WORK ENG');
        cy.get('#root_payment_method').select('Bank Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
        cy.get('#root_item_0_sub_category').select('coworking');
        cy.get('#root_item_0_item_name').clear().type('Coworking is not only about providing a physical place, but also about establishing a community');
        cy.get('#root_item_0_qty').clear().type('5');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('EUR');
        cy.get('#root_item_0_unit_price').type('250');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get("input[type=file]")
          .attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get("input[type=file]")
          .attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);

        cy.get("input[type=file]")
          .attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);

        cy.get("input[type=file]")
          .attachFile(['sampletext.txt']);

        cy.wait(2000);

        //cy.contains('Submit the Request').click();

        //cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        cy.get('button')
          .contains(/^Return to Home$/)
          .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
        cy.wait(1000);

        let budgetOwnerUsername = Cypress.env('budgetowner_username');
        let budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log('=====budgetOwnerUsername : ' + budgetOwnerUsername);
        cy.log('=====budgetOwnerPassword : ' + budgetOwnerPassword);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          "reject"
        );

      });
    });

    //Budget owner request for additional details
    it('Budget owner need more info', () => {
      let username = Cypress.env('requestor_username');
      let password = Cypress.env('requestor_password');
      cy.log('=====username : ' + username);
      cy.log('=====password : ' + password);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services');

      cy.runPrimaryBpmnFile(true);

      /* cy.contains('Please select the type of request to start the process.');
       // wait a second to ensure we can click the radio button
 
       cy.wait(2000);
       cy.get('input#root-procurement').click();
       cy.wait(2000);
 
 
       cy.get('button')
         .contains(/^Submit$/)
         .click();
 */

      cy.contains(
        'Request Goods or Services',
        { timeout: 60000 }
      );

       cy.wait(5000);
            cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('other_fees');
        cy.get('#root_purpose').clear().type('It allows cost savings and convenience through the use of common infrastructures, such as equipment, utilities and receptionist and custodial services, and in some cases refreshments and parcel services.\nhttps://en.wikipedia.org/wiki/Coworking');
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('12-02-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('BOUNTY');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
        cy.get('#root_item_0_sub_category').select('bounties');
        cy.get('#root_item_0_item_name').clear().type('Coworking is distinct from business accelerators, business incubators, and executive suites.');
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('450');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('It\’s free and easy to post a job. Simply fill in a title, description and budget and competitive bids come within minutes. No job is too big or too small. We\'ve got freelancers for jobs of any size or budget across 1800 skills. No job is too complex.');

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get("input[type=file]")
          .attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get("input[type=file]")
          .attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);

        cy.get("input[type=file]")
          .attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get('#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);
        cy.get('#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg').click();
        cy.wait(1000);

        cy.get("input[type=file]")
          .attachFile(['sampletext.txt']);

        cy.wait(2000);

        //cy.contains('Submit the Request').click();

        //cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        cy.get('button')
          .contains(/^Return to Home$/)
          .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
        cy.wait(1000);

        let budgetOwnerUsername = Cypress.env('budgetowner_username');
        let budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log('=====budgetOwnerUsername : ' + budgetOwnerUsername);
        cy.log('=====budgetOwnerPassword : ' + budgetOwnerPassword);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          "needmoreinfo"
        );

        //requestor sending additional info
        submitWithUser(
          username,
          password,
          processInstanceId,
          null,
          "providemoreinfo"
        );

        //budget owner approves second time
        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          "approve"
        );

      });
    });

  });
});