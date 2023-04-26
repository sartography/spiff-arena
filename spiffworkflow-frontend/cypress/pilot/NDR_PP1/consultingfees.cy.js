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
    cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' needs additional info. A software license is a document that provides legally binding guidelines for the use and distribution of software.Software licenses typically provide end users with the right to END.'));
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

    cy.get('.cds--text-area__wrapper').find('#root').clear().type('Providing additional info. It\’s free and easy to post a job. Simply fill in a title, description and budget and competitive bids come within minutes. No job is too big or too small. We\'ve got people for jobs of any size.');

    cy.contains('Submit the Request').click();
    cy.get('input[value="Submit the Request"]').click();

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

//Consulting Fees Path - Without Files
describe('Consulting Fees Path - Without Files', () => {
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

      /*      cy.contains('Please select the type of request to start the process.');
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

      cy.wait(15000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks

        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose').clear().type('Consulting ==== Management consulting includes a broad range of activities, and the many firms and their members often define these practices quite differently. One way to categorize the activities is in terms of the professional’s area of expertise.');
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-12-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Embassar');
        cy.get('#root_payment_method').select('Bank Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });*/
        //item 0
        cy.get('#root_item_0_sub_category').select('ambassadors');
        cy.get('#root_item_0_item_name').clear().type('An ambassador is an official envoy, especially a high-ranking diplomat who represents a state.');
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('ETH');
        cy.get('#root_item_0_unit_price').type('1.15');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name').clear().type('Find & hire top freelancers, web developers & designers inexpensively. ');
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, \‘consultant\’ and advisor\’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

        cy.contains('Submit the Request').click();

        cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.visit('/');

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

      /*      cy.contains('Please select the type of request to start the process.');
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

      cy.wait(15000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose').clear().type('Consulting is defined as the practise of providing a third party with expertise on a matter in exchange for a fee. The service may involve either advisory or implementation services.');
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('24-10-2032');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Consultancy.uk');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });*/

        //Item 0
        cy.get('#root_item_0_sub_category').select('consultants');
        cy.get('#root_item_0_item_name').clear().type('Software development consultants with Python background');
        cy.get('#root_item_0_qty').clear().type('5');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('DAI');
        cy.get('#root_item_0_unit_price').type('1500');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name').clear().type('Find & hire top freelancers, web developers & designers inexpensively. ');
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

        cy.contains('Submit the Request').click();

        cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.visit('/');

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

      /*      cy.contains('Please select the type of request to start the process.');
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

      cy.wait(15000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose').clear().type('Freelancing - Freelancing is doing specific work for clients without committing to full-time employment. Freelancers often take on multiple projects with different clients simultaneously. IRS considers freelancers to be self-employed individuals.');
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('05-04-2028');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Upwork');
        cy.get('#root_payment_method').select('Debit Card');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });*/

        //item 0
        cy.get('#root_item_0_sub_category').select('freelancers');
        cy.get('#root_item_0_item_name').clear().type('Freelancers to do the Python development and front end react app development');
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1750');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name').clear().type('Find & hire top freelancers, web developers & designers inexpensively. ');
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');



        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper').find('#root').type('It\’s free and easy to post a job. Simply fill in a title, description and budget and competitive bids come within minutes. No job is too big or too small. We\'ve got freelancers for jobs of any size or budget across 1800 skills. No job is too complex.');

        cy.contains('Submit the Request').click();

        cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.visit('/');

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

//Consulting Fees Path - With Files
describe('Consulting Fees Path - With Files', () => {
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

      /*      cy.contains('Please select the type of request to start the process.');
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

      cy.wait(15000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose').clear().type('Consulting ==== Management consulting includes a broad range of activities, and the many firms and their members often define these practices quite differently. One way to categorize the activities is in terms of the professional’s area of expertise.');
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('05-12-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Embassar');
        cy.get('#root_payment_method').select('Bank Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });*/

        //item 0
        cy.get('#root_item_0_sub_category').select('ambassadors');
        cy.get('#root_item_0_item_name').clear().type('An ambassador is an official envoy, especially a high-ranking diplomat who represents a state.');
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('ETH');
        cy.get('#root_item_0_unit_price').type('1.15');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name').clear().type('Find & hire top freelancers, web developers & designers inexpensively. ');
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');


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

        cy.contains('Submit the Request').click();

        cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        cy.visit('/');
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

      /*      cy.contains('Please select the type of request to start the process.');
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

      cy.wait(15000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose').clear().type('Consulting is defined as the practise of providing a third party with expertise on a matter in exchange for a fee. The service may involve either advisory or implementation services.');
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('14-10-2029');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Consultancy.uk');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });*/

        //item 0
        cy.get('#root_item_0_sub_category').select('consultants');
        cy.get('#root_item_0_item_name').clear().type('Software development consultants with Python background');
        cy.get('#root_item_0_qty').clear().type('5');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('DAI');
        cy.get('#root_item_0_unit_price').type('1500');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name').clear().type('Find & hire top freelancers, web developers & designers inexpensively. ');
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');


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

        cy.contains('Submit the Request').click();

        cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        cy.visit('/');

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

      /*      cy.contains('Please select the type of request to start the process.');
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

      cy.wait(15000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        let projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose').clear().type('Freelancing - Freelancing is doing specific work for clients without committing to full-time employment. Freelancers often take on multiple projects with different clients simultaneously. IRS considers freelancers to be self-employed individuals.');
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('05-04-2024');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Upwork');
        cy.get('#root_payment_method').select('Debit Card');
        /*cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains('Task: Enter NDR Items', { timeout: 60000 });*/
        //item 0
        cy.get('#root_item_0_sub_category').select('freelancers');
        cy.get('#root_item_0_item_name').clear().type('Freelancers to do the Python development and front end react app development');
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1750');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name').clear().type('A consultant (from Latin: consultare "to deliberate") is a professional');
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        //item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name').clear().type('Find & hire top freelancers, web developers & designers inexpensively. ');
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');


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

        cy.contains('Submit the Request').click();

        cy.get('input[value="Submit the Request"]').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();
        cy.wait(6000);
        cy.visit('/');
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


