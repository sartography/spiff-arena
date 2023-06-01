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
  if (approvaltype === 'approve') {
    cy.get('#root > label:nth-child(1)').click();
    cy.get('.cds--text-area__wrapper')
      .find('#root')
      .type(username.concat(' is approving this.'));
  } else if (approvaltype === 'reject') {
    cy.get('#root > label:nth-child(3)').click();
    cy.get('.cds--text-area__wrapper')
      .find('#root')
      .type(username.concat(' is rejecting this.'));
  } else if (approvaltype === 'needmoreinfo') {
    cy.get('#root > label:nth-child(2)').click();
    cy.get('.cds--text-area__wrapper')
      .find('#root')
      .type(
        username.concat(
          ' needs additional info. The term, learning and development, encompasses any professional development a business provides to its employees END.'
        )
      );
  } else if (approvaltype === 'providemoreinfo') {
    // Form 1
    cy.contains('Task: Submit Details', { timeout: 60000 });
    cy.get('button')
      .contains(/^Submit$/)
      .click();
    // Form 2
    /* cy.contains('Task: Enter NDR Items', { timeout: 60000 });
        cy.get('button')
            .contains(/^Submit$/)
            .click(); */
    // Form 3
    cy.contains('Task: Review the Request', { timeout: 60000 });

    cy.get('.cds--text-area__wrapper')
      .find('#root')
      .clear()
      .type(
        'Providing additional info. Learning and development (L&D) is a function within an organization that is responsible for empowering employees’ growth and developing their knowledge, skills, and capabilities to drive better business performance.'
      );

    // cy.contains('Submit the Request').click();
    // cy.get('input[value="Submit the Request"]').click();
  } else {
  }

  cy.get('button')
    .contains(/^Submit$/)
    .click();

  // if (expectAdditionalApprovalInfoPage) {
  //   cy.contains(expectAdditionalApprovalInfoPage, { timeout: 60000 });

  //   cy.get('button')
  //     .contains(/^Continue$/)
  //     .click();
  // }

  cy.wait(5000);
  cy.contains('Process Instance Id:', { timeout: 60000 });
  cy.logout();

};

//Check if the process instance is completed successfully
const checkProcessInstanceCompleted = (
  username,
  password,
  processInstanceId
) => {
  cy.wait(2000);
  cy.log('========Login with : ', username);
  cy.log('========processInstanceId: ', processInstanceId);
  cy.login(username, password);

  cy.wait(1000);
  cy.visit('/admin/process-instances/find-by-id');
  cy.get('#process-instance-id-input').type(processInstanceId);

  cy.get('button')
    .contains(/^Submit$/)
    .click();

  cy.wait(2000);
  cy.get('#tag-1 > span').contains('complete');
}

// Learning and Development Path - Without Files
describe.only('Learning and Development Path - Without Files', () => {
  Cypress._.times(1, () => {
    // People Ops Partner Group approves the request
    it('Books Only. People Ops Partner Group approves', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('05-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('AIHR');
        cy.get('#root_payment_method').select('Debit Card');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('books');
        cy.get('#root_item_0_item_name')
          .clear()
          .type('A bounty is a payment or reward of money to locate');
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // People Ops Partner Group rejects the request
    it('Books Only. People Ops Partner Group rejects', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Learning and development (L&D) is a function within an organization that is responsible for empowering employees’ growth and developing their knowledge, skills, and capabilities to drive better business performance. '
          );
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('24-02-2026');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('EYK Books');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('books');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'The role of the L&D function has evolved to meet the demands of digital transformation and a modern.'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'The function may be organized centrally, either independently or sitting under human resources (HR); decentralized throughout different business units; or be a hybrid (sometimes referred to as federated) structure.'
          );

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'reject'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // People Ops Partner Group request for additional details
    it('Books Only. People Ops Partner Group needs more info', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'A comprehensive collection of the concepts, definitions, and methodologies for the profession can be found in the. \nhttps://www.aihr.com/blog/learning-and-development/'
          );
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('25-02-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('BOUNTY');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('books');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'There are many different roles that make up a learning and development team or fall under the umbrel'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'Current and aspiring talent development professionals can enhance their skills with the various professional education courses offered by ATD Education \nhttps://www.aihr.com/blog/learning-and-development/'
          );

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'needmoreinfo'
        );

        // requestor sending additional info
        submitWithUser(
          username,
          password,
          processInstanceId,
          null,
          'providemoreinfo'
        );

        // people ops approves second time
        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // Budget owner approves and People Ops Partner Group approves the request
    it('NOT Books Only. Budget owner approves and People Ops Partner Group approves', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'In 2019, the Association for Talent Development (ATD) conducted a competency study to assess needed talent development capabilities. The research found that the knowledge, skills, and attitudes (KSAs) of effective talent development professionals'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Lynda.com');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('on_conf');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'The goal of learning and development is to develop or change the behavior of individuals or groups'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('course');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'The goal of learning and development is to change the behavior of individuals or groups for better'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Crypto');
        cy.get('#root_item_1_currency').select('DAI');
        cy.get('#root_item_1_unit_price').type('2450');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 2
        cy.get('#root_item_2_sub_category').select('books');
        cy.get('#root_item_2_item_name')
          .clear()
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        const budgetOwnerUsername = Cypress.env('budgetowner_username');
        const budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log(`=====budgetOwnerUsername : ${budgetOwnerUsername}`);
        cy.log(`=====budgetOwnerPassword : ${budgetOwnerPassword}`);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          'approve'
        );

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // Budget owner rejects the request
    it('NOT Books Only. Budget owner rejects', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('24-02-2026');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Udemy Courses');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('course');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'There are many different roles that make up a learning and development team or fall under the'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const budgetOwnerUsername = Cypress.env('budgetowner_username');
        const budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log(`=====budgetOwnerUsername : ${budgetOwnerUsername}`);
        cy.log(`=====budgetOwnerPassword : ${budgetOwnerPassword}`);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          'reject'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // Budget owner request for additional details
    it('NOT Books Only. Budget owner needs more info', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Research found that the knowledge, skills, and attitudes (KSAs) of effective talent development professionals, at every level of their career, fell into three major domains of practice.'
          );
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('25-02-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Conference LTD');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('on_conf');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const budgetOwnerUsername = Cypress.env('budgetowner_username');
        const budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log(`=====budgetOwnerUsername : ${budgetOwnerUsername}`);
        cy.log(`=====budgetOwnerPassword : ${budgetOwnerPassword}`);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          'needmoreinfo'
        );

        // requestor sending additional info
        submitWithUser(
          username,
          password,
          processInstanceId,
          null,
          'providemoreinfo'
        );

        // budget owner approves second time
        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          'approve'
        );

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );

        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });
  });
});

// Learning and Development Path - With Files
describe('Learning and Development Path - With Files', () => {
  Cypress._.times(1, () => {
    // People Ops Partner Group approves the request
    it('Books Only. People Ops Partner Group approves', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Training Industry');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('books');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get('input[type=file]').attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get('input[type=file]').attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['sampletext.txt']);

        cy.wait(2000);

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // People Ops Partner Group rejects the request
    it('Books Only. People Ops Partner Group rejects', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'The goal of learning and development is to develop or change the behavior of individuals or groups for the better, sharing knowledge and insights that enable them to do their work better, or cultivate attitudes that help them perform better'
          );
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('04-02-2026');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('EYK Books');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('books');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'There are many different roles that make up a learning and development team or fall'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get('input[type=file]').attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get('input[type=file]').attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['sampletext.txt']);

        cy.wait(2000);

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'reject'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // People Ops Partner Group request for additional details
    it('Books Only. People Ops Partner Group needs more info', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('05-02-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Conference LTD');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('books');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'Learning, training, and development are often used interchangeably. However, there are subtle differences between these concepts, which are shown in the table below. \nhttps://www.aihr.com/blog/learning-and-development/'
          );

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get('input[type=file]').attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get('input[type=file]').attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['sampletext.txt']);

        cy.wait(2000);
        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'needmoreinfo'
        );

        // requestor sending additional info
        submitWithUser(
          username,
          password,
          processInstanceId,
          null,
          'providemoreinfo'
        );

        // people ops approves second time
        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // Budget owner approves and People Ops Partner Group approves the request
    it('NOT Books Only. Budget owner approves and People Ops Partner Group approves', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('05-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('The Leadership Laboratory');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /* cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                
                cy.contains('Task: Enter NDR Items', { timeout: 60000 }); */
        // item 0
        cy.get('#root_item_0_sub_category').select('on_conf');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'There are many different roles that make up a learning and development team'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('course');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'The goal of learning and development is to change the behavior of individuals or groups for better'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 2
        cy.get('#root_item_2_sub_category').select('books');
        cy.get('#root_item_2_item_name')
          .clear()
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get('input[type=file]').attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get('input[type=file]').attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['png-5mb-2.png']);

        cy.wait(2000);

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        const budgetOwnerUsername = Cypress.env('budgetowner_username');
        const budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log(`=====budgetOwnerUsername : ${budgetOwnerUsername}`);
        cy.log(`=====budgetOwnerPassword : ${budgetOwnerPassword}`);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          'approve'
        );

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // Budget owner rejects the request
    it('NOT Books Only. Budget owner rejects', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'The goal of learning and development is to develop or change the behavior of individuals or groups for the better, sharing knowledge and insights that enable them to do their work better, or cultivate attitudes that help them perform better'
          );
        cy.get('#root_criticality').select('Medium');
        cy.get('#root_period').clear().type('14-02-2026');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Lynda.com');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('course');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'The goal of learning and development is to develop or change the behavior of individuals or groups'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'Learning and development is a systematic process to enhance an employee’s skills, knowledge, and competency, resulting in better performance in a work setting. \nhttps://www.aihr.com/blog/learning-and-development/'
          );

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get('input[type=file]').attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get('input[type=file]').attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['sampletext.txt']);

        cy.wait(2000);

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const budgetOwnerUsername = Cypress.env('budgetowner_username');
        const budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log(`=====budgetOwnerUsername : ${budgetOwnerUsername}`);
        cy.log(`=====budgetOwnerPassword : ${budgetOwnerPassword}`);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          'reject'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });

    // Budget owner request for additional details
    it('NOT Books Only. Budget owner needs more info', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

      /*            cy.contains('Please select the type of request to start the process.');
                        // wait a second to ensure we can click the radio button
            
                        cy.wait(2000);
                        cy.get('input#root-procurement').click();
                        cy.wait(2000);
            
            
                        cy.get('button')
                            .contains(/^Submit$/)
                            .click();
            */

      cy.contains('Request Goods or Services', { timeout: 60000 });

      // cy.wait(5000);
      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('learn_and_dev');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Learning, training, and development are often used interchangeably. However, there are subtle differences between these concepts, which are shown in the table below. '
          );
        cy.get('#root_criticality').select('Low');
        cy.get('#root_period').clear().type('15-02-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Conference LTD');
        cy.get('#root_payment_method').select('Crypto Transfer');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('on_conf');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'There are many different roles that make up a learning and development team'
          );
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

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'A L&D strategy should be aligned to the organization’s business strategy and goals with the aim of developing the workforce’s capability and driving business results.'
          );

        cy.get('#root > div:nth-child(3) > p > button').click();

        cy.get('input[type=file]').attachFile(['lorem-ipsum.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get('input[type=file]').attachFile(['png-5mb-1.png']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['Free_Test_Data_1MB_PDF.pdf']);
        cy.wait(1000);

        cy.get('#root > div:nth-child(3) > p > button').click();
        cy.wait(1000);

        cy.get(
          '#root > div.row.array-item-list > div:nth-child(4) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);
        cy.get(
          '#root > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up > svg'
        ).click();
        cy.wait(1000);

        cy.get('input[type=file]').attachFile(['sampletext.txt']);

        cy.wait(2000);

        // cy.contains('Submit the Request').click();

        // cy.get('input[value="Submit the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(9000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);

        const budgetOwnerUsername = Cypress.env('budgetowner_username');
        const budgetOwnerPassword = Cypress.env('budgetowner_password');
        cy.log(`=====budgetOwnerUsername : ${budgetOwnerUsername}`);
        cy.log(`=====budgetOwnerPassword : ${budgetOwnerPassword}`);

        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          null,
          'needmoreinfo'
        );

        // requestor sending additional info
        submitWithUser(
          username,
          password,
          processInstanceId,
          null,
          'providemoreinfo'
        );

        // budget owner approves second time
        submitWithUser(
          budgetOwnerUsername,
          budgetOwnerPassword,
          processInstanceId,
          'Task: Reminder: Check Existing Budget',
          'approve'
        );

        const peopleOpsUsername = Cypress.env('peopleopssme_username');
        const peopleOpsPassword = Cypress.env('peopleopssme_password');
        cy.log(`=====peopleOpsUsername : ${peopleOpsUsername}`);
        cy.log(`=====peopleOpsPassword : ${peopleOpsPassword}`);

        submitWithUser(
          peopleOpsUsername,
          peopleOpsPassword,
          processInstanceId,
          null,
          'approve'
        );
        checkProcessInstanceCompleted(username, password, processInstanceId);
      });
    });
  });
});
