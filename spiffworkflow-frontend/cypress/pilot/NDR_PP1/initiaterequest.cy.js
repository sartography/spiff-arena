const submitWithUserSpecialChars = (
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
      .type(username.concat(' is approving this. Providing additional info with Special chars <>?,./ afsfsf : sf; sdf"sfs" fdsf\'sdf sfds{ sfsf [ s} } \s ss !@#$%^&*()_+ sff =-~ ` END.'), { parseSpecialCharSequences: false });
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
          ' needs additional info. A software license is a document that provides legally binding guidelines for the use and distribution of software.Software licenses typically provide end users with the right to END.'
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
        'Providing additional info with Special chars <>?,./ afsfsf : sf; sdf"sfs" fdsf\'sdf sfds{ sfsf [ s} } \s ss !@#$%^&*()_+ sff =-~ ` END.,', { parseSpecialCharSequences: false }
      );

    // cy.contains('Submit the Request').click();
    // cy.get('input[value="Submit the Request"]').click();
  } else {
  }


  cy.contains(
    'Purpose is to test all the special characters work in the request. ~!@#$%^&*()_+`-= {}[]\ and ;\',./:"<>? end.'
  );
  cy.contains(
    /^Consulting Fees$/
  );
  cy.contains(
    /^Medium$/
  );
  cy.contains(
    /^24-10-2032$/
  );
  cy.contains(
    /^Consultancy.uk$/
  );
  cy.contains(
    /^Crypto Transfer$/
  );
  cy.contains(
    'Special char test ,./;\'[]\=-0987654321`~!@#$%^&*()_+{}:"<>? end.'
  );
  cy.contains(
    /^Consultants$/
  );
  cy.contains(
    /^23$/
  );
  cy.contains(
    /^SNT$/
  );
  cy.contains(
    /^1,915.0000$/
  );
  cy.contains(
    'Special char test 2 +_=)(*&^%$#@!~`?></.,":}{\][\';/., <a> {g} [a]end.'
  );
  cy.contains(
    /^Freelancers$/
  );
  cy.contains(
    /^15$/
  );
  cy.contains(
    /^AED$/
  );
  cy.contains(
    /^4,537.25$/
  );
  cy.contains(
    'Test Special chars afs<sfsd>sfsfs,asfdf. sfsf? sfd/sfs f:sfsf " sfsdf; SDFfsd\' sfsdf{sfsfs} sfsdf[ sfsdf] fsfsfd\ sfsd sfsdf=S dfs+ sfd- sfsdf_ sfsfd (sfsd )sfsfsd * sf&sfsfs ^ sfs % sf $ ss# s@ sf! sfd` ss~ END.'
  );

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
const checkProcessInstanceCompletedSpecialChars = (
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

  cy.contains(
    /^Process Recap$/
  );
  cy.contains(
    /^Approval Status: Approved$/
  );

  cy.contains(
    'Purpose is to test all the special characters work in the request. ~!@#$%^&*()_+`-= {}[]\ and ;\',./:"<>? end.'
  );
  cy.contains(
    /^Consulting Fees$/
  );
  cy.contains(
    /^Medium$/
  );
  cy.contains(
    /^24-10-2032$/
  );
  cy.contains(
    /^Consultancy.uk$/
  );
  cy.contains(
    /^Crypto Transfer$/
  );
  cy.contains(
    'Special char test ,./;\'[]\=-0987654321`~!@#$%^&*()_+{}:"<>? end.'
  );
  cy.contains(
    /^Consultants$/
  );
  cy.contains(
    /^23$/
  );
  cy.contains(
    /^SNT$/
  );
  cy.contains(
    /^1,915.0000$/
  );
  cy.contains(
    'Special char test 2 +_=)(*&^%$#@!~`?></.,":}{\][\';/., <a> {g} [a]end.'
  );
  cy.contains(
    /^Freelancers$/
  );
  cy.contains(
    /^15$/
  );
  cy.contains(
    /^AED$/
  );
  cy.contains(
    /^4,537.25$/
  );
  cy.contains(
    'Test Special chars afs<sfsd>sfsfs,asfdf. sfsf? sfd/sfs f:sfsf " sfsdf; SDFfsd\' sfsdf{sfsfs} sfsdf[ sfsdf] fsfsfd\ sfsd sfsdf=S dfs+ sfd- sfsdf_ sfsfd (sfsd )sfsfsd * sf&sfsfs ^ sfs % sf $ ss# s@ sf! sfd` ss~ END.'
  );
  cy.contains(
    'Providing additional info with Special chars <>?,./ afsfsf : sf; sdf"sfs" fdsf\'sdf sfds{ sfsf [ s} } \s ss !@#$%^&*()_+ sff =-~ ` END.'
  );
  cy.contains(
    'Budget Owner '
  );
}

// Software and License - Without Files
describe('Initiate a Request - Without Files', () => {
  Cypress._.times(1, () => {
    // Submit a Software and License request - Without Files
    it('1.Submit a Software and License request', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
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
      });
    });

    // Submit a Software and License request - Without Files and with mandatory fields only
    it('2.Submit a Software and License request - Without Files and with mandatory fields only', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose').clear().type('Need to buy a Software');
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('24-11-2025');
        cy.get('body').click();
        // cy.get('#root_vendor').clear().type('Embassar');
        // cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name').clear().type('Open source software');
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('USD');
        cy.get('#root_item_0_unit_price').type('550');

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

        // cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

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
      });
    });

    // Edit a Software and License request - Without Files
    it('3.Edit a Software and License request', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915.2456');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S,\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
          );

        // cy.contains('Edit the Request').click();

        // cy.get('input[value="Edit the Request"]').click();

        cy.get('button')
          .contains(/^Edit Request$/)
          .click();

        // Form 1
        cy.contains('Task: Submit Details', { timeout: 60000 });

        cy.contains('Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
        cy.contains('High');
        cy.contains('25-11-2025');
        cy.contains('Microsoft');
        cy.contains('Reimbursement');
        cy.contains('Open source software is code that is designed to be publicly accessible anyone can see, modify, END');
        cy.contains('2');
        cy.contains('Crypto');
        cy.contains('SNT');
        cy.contains('1915.2456');
        cy.contains('A software license is a document that provides legally binding guidelines for the use and distri END');
        cy.contains('1');
        cy.contains('Fiat');
        cy.contains('AED');
        cy.contains('4500');

        cy.wait(2000);
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

        cy.contains('2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S,\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows', { timeout: 1000 });

        cy.get('.cds--text-area__wrapper').find('#root').type('EDITING INFO');

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.logout();
        cy.wait(2000);
      });
    });

    // Save and Close a Software and License request 1 - Without Files
    it('4.Save and Close a Software and License request 1', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

        cy.get('button')
          .contains(/^Save and Close$/)
          .click();

        // cy.get('button')
        //    .contains(/^Return to Home$/)
        //    .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
      });
    });

    // Save and Close a Software and License request 2 - Without Files
    it('5.Save and Close a Software and License request 2', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        // cy.get('#root_item_1_qty').clear().type('1');
        // cy.get('#root_item_1_currency_type').select('Fiat');
        // cy.get('#root_item_1_currency').select('AED');
        // cy.get('#root_item_1_unit_price').type('4500');

        cy.get('button')
          .contains(/^Save and Close$/)
          .click();

        // cy.get('button')
        //    .contains(/^Return to Home$/)
        //    .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
      });
    });

    // Save and Close a Software and License request 3 - Without Files
    it('6.Save and Close a Software and License request 3', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
          );

        cy.get('button')
          .contains(/^Save and Close$/)
          .click();

        // cy.get('button')
        //     .contains(/^Return to Home$/)
        //     .click();

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
      });
    });

    // Cancel a Software and License request 1- Without Files
    it('7.Cancel a Software and License request 1', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

        // cy.get('#root-Yes').click();

        cy.get('button')
          .contains(/^Cancel Request$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
      });
    });

    // Cancel a Software and License request 2- Without Files
    it('8.Cancel a Software and License request 2', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
          );

        // cy.contains('Cancel the Request').click();

        // cy.get('input[value="Cancel the Request"]').click();

        cy.get('button')
          .contains(/^Cancel Request$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
      });
    });

    // Arrange items order
    it('9.Arrange items order', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

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
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Consulting ==== Management consulting includes a broad range of activities, and the many firms and their members often define these practices quite differently. One way to categorize the activities is in terms of the professional’s area of expertise.'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-12-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Embassar');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
          .contains(/^Submit$/)
          .click();
 
        cy.contains('Task: Enter NDR Items', { timeout: 60000 }); */
        // item 0
        cy.get('#root_item_0_sub_category').select('ambassadors');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            '1. An ambassador is an official envoy, especially a high-ranking diplomat who represents a.'
          );
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('ETH');
        cy.get('#root_item_0_unit_price').type('1.15');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            '2. A consultant (from Latin: consultare "to deliberate") is a professional'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name')
          .clear()
          .type(
            '3. Find & hire top freelancers, web developers & designers inexpensively. '
          );
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 3
        cy.get('#root_item_3_sub_category').select('consultants');
        cy.get('#root_item_3_item_name')
          .clear()
          .type(
            '4. The term supercomputer does not refer to a specific technology.'
          );
        cy.get('#root_item_3_qty').clear().type('6');
        cy.get('#root_item_3_currency_type').select('Crypto');
        cy.get('#root_item_3_currency').select('DAI');
        cy.get('#root_item_3_unit_price').type('1500.1234');

        cy.get('#root_item > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up').click();
        cy.get('#root_item > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up').click();

        cy.wait(2000);

        cy.get('#root_item > div.row.array-item-list > div:nth-child(1) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-down').click();
        cy.get('#root_item > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-down').click();


        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

      });
    });

    // Delete items
    it('10.Delete items', () => {
      const username = Cypress.env('requestor_username');
      const password = Cypress.env('requestor_password');
      cy.log(`=====username : ${username}`);
      cy.log(`=====password : ${password}`);

      cy.login(username, password);
      cy.visit('/');

      cy.contains('Start New +').click();
      cy.contains('Request Goods or Services').click();

      cy.runPrimaryBpmnFile(true);

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
        cy.get('#root_category').select('consult_fees');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Consulting ==== Management consulting includes a broad range of activities, and the many firms and their members often define these practices quite differently. One way to categorize the activities is in terms of the professional’s area of expertise.'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-12-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Embassar');
        cy.get('#root_payment_method').select('Bank Transfer');
        /* cy.get('button')
          .contains(/^Submit$/)
          .click();
 
        cy.contains('Task: Enter NDR Items', { timeout: 60000 }); */
        // item 0
        cy.get('#root_item_0_sub_category').select('ambassadors');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            '1. An ambassador is an official envoy, especially a high-ranking diplomat who represents a.'
          );
        cy.get('#root_item_0_qty').clear().type('4');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('ETH');
        cy.get('#root_item_0_unit_price').type('1.15');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('consultants');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            '2. A consultant (from Latin: consultare "to deliberate") is a professional'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('CAD');
        cy.get('#root_item_1_unit_price').type('1355');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 2
        cy.get('#root_item_2_sub_category').select('freelancers');
        cy.get('#root_item_2_item_name')
          .clear()
          .type(
            '3. Find & hire top freelancers, web developers & designers inexpensively. '
          );
        cy.get('#root_item_2_qty').clear().type('6');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('SNT');
        cy.get('#root_item_2_unit_price').type('2300');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 3
        cy.get('#root_item_3_sub_category').select('consultants');
        cy.get('#root_item_3_item_name')
          .clear()
          .type(
            '4. The term supercomputer does not refer to a specific technology.'
          );
        cy.get('#root_item_3_qty').clear().type('6');
        cy.get('#root_item_3_currency_type').select('Crypto');
        cy.get('#root_item_3_currency').select('DAI');
        cy.get('#root_item_3_unit_price').type('1500.1234');

        //delete first and third items
        cy.get('#root_item > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-danger.array-item-remove').click();
        cy.get('#root_item > div.row.array-item-list > div:nth-child(1) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-danger.array-item-remove').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.contains(
          'Review and provide any supporting information or files for your request.',
          { timeout: 60000 }
        );

      });
    });
  });
});

// Form validation - Software and License - Without Files
describe('Form validation', () => {

  //Special character check
  it('11.Special character check', () => {
    const username = Cypress.env('requestor_username');
    const password = Cypress.env('requestor_password');
    cy.log(`=====username : ${username}`);
    cy.log(`=====password : ${password}`);

    cy.login(username, password);
    cy.visit('/');

    cy.contains('Start New +').click();
    cy.contains('Request Goods or Services').click();

    cy.runPrimaryBpmnFile(true);

    cy.contains('Request Goods or Services', { timeout: 60000 });

    cy.url().then((currentUrl) => {
      // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
      // extract the digits after /tasks
      const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
      cy.log('==###############===processInstanceId : ', processInstanceId);
      const projectId = Cypress.env('project_id');
      cy.get('#root_project').select(projectId);
      cy.get('#root_category').select('consult_fees');
      cy.get('#root_purpose')
        .clear()
        .type(
          'Purpose is to test all the special characters work in the request. ~!@#$%^&*()_+`-= {}[]\ and ;\',./:"<>? end. | this text goes missing', { parseSpecialCharSequences: false }
        );

      //.type(
      //  'Purpose is to test all the special characters work in the request. Test Special chars ~!@#$%^&*()_+`-= {}|[]\ and ;\',./:"<>? end.', { parseSpecialCharSequences: false }
      //);

      cy.get('#root_criticality').select('Medium');
      cy.get('#root_period').clear().type('24-10-2032');
      cy.get('body').click();
      cy.get('#root_vendor').clear().type('Consultancy.uk');
      cy.get('#root_payment_method').select('Crypto Transfer');

      // item 0
      cy.get('#root_item_0_sub_category').select('consultants');
      cy.get('#root_item_0_item_name')
        .clear()
        .type(
          'Special char test ,./;\'[]\=-0987654321`~!@#$%^&*()_+{}:"<>? end.', { parseSpecialCharSequences: false }
        );
      //.type(
      //  'Special char test ,./;\'[]\=-0987654321`~!@#$%^&*()_+{}|:"<>? end.', { parseSpecialCharSequences: false }
      // );
      cy.get('#root_item_0_qty').clear().type('23');
      cy.get('#root_item_0_currency_type').select('Crypto');
      cy.get('#root_item_0_currency').select('SNT');
      cy.get('#root_item_0_unit_price').type('1915');

      cy.get('#root_item > div:nth-child(3) > p > button').click();

      // item 1
      cy.get('#root_item_1_sub_category').select('freelancers');
      cy.get('#root_item_1_item_name')
        .clear()
        .type(
          'Special char test 2 +_=)(*&^%$#@!~`?></.,":}{\][\';/., <a> {g} [a]end.', { parseSpecialCharSequences: false }
        );
      //.type(
      //  'Special char test 2 +_=)(*&^%$#@!~`?></.,":}{|\][\';/., <a> {g} [a]end.', { parseSpecialCharSequences: false }
      //);
      cy.get('#root_item_1_qty').clear().type('15');
      cy.get('#root_item_1_currency_type').select('Fiat');
      cy.get('#root_item_1_currency').select('AED');
      cy.get('#root_item_1_unit_price').type('4537.25');

      cy.get('button')
        .contains(/^Submit$/)
        .click();

      cy.contains(
        'Review and provide any supporting information or files for your request.',
        { timeout: 60000 }
      );


      cy.contains(
        'Purpose is to test all the special characters work in the request. ~!@#$%^&*()_+`-= {}[]\ and ;\',./:"<>? end.'
      );
      cy.contains(
        /^Consulting Fees$/
      );
      cy.contains(
        /^Medium$/
      );
      cy.contains(
        /^24-10-2032$/
      );
      cy.contains(
        /^Consultancy.uk$/
      );
      cy.contains(
        /^Crypto Transfer$/
      );
      cy.contains(
        'Special char test ,./;\'[]\=-0987654321`~!@#$%^&*()_+{}:"<>? end.'
      );
      cy.contains(
        /^Consultants$/
      );
      cy.contains(
        /^23$/
      );
      cy.contains(
        /^SNT$/
      );
      cy.contains(
        /^1,915.0000$/
      );
      cy.contains(
        'Special char test 2 +_=)(*&^%$#@!~`?></.,":}{\][\';/., <a> {g} [a]end.'
      );
      cy.contains(
        /^Freelancers$/
      );
      cy.contains(
        /^15$/
      );
      cy.contains(
        /^AED$/
      );
      cy.contains(
        /^4,537.25$/
      );

      cy.get('.cds--text-area__wrapper')
        .find('#root')
        .type(
          'Test Special chars afs<sfsd>sfsfs,asfdf. sfsf? sfd/sfs f:sfsf " sfsdf; SDFfsd\' sfsdf{sfsfs} sfsdf[ sfsdf] fsfsfd\ sfsd sfsdf=S dfs+ sfd- sfsdf_ sfsfd (sfsd )sfsfsd * sf&sfsfs ^ sfs % sf $ ss# s@ sf! sfd` ss~ END.', { parseSpecialCharSequences: false }
        );
      //.type(
      //  'Test Special chars afs<sfsd>sfsfs,asfdf. sfsf? sfd/sfs f:sfsf " sfsdf; SDFfsd\' sfsdf{sfsfs} sfsdf[ sfsdf] fsfsfd\ sfsd| sfsdf=S dfs+ sfd- sfsdf_ sfsfd (sfsd )sfsfsd * sf&sfsfs ^ sfs % sf $ ss# s@ sf! sfd` ss~ END.', { parseSpecialCharSequences: false }
      //);

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

      submitWithUserSpecialChars(
        budgetOwnerUsername,
        budgetOwnerPassword,
        processInstanceId,
        'Task: Reminder: Check Existing Budget',
        'approve'
      );

      checkProcessInstanceCompletedSpecialChars(username, password, processInstanceId);
    });
  });

  //Check field max lengths
  it('12.Check field max lengths', () => {
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

    cy.url().then((currentUrl) => {
      // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
      // extract the digits after /tasks
      const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
      cy.log('==###############===processInstanceId : ', processInstanceId);
      const projectId = Cypress.env('project_id');
      cy.wait(2000);
      cy.get('#root_project').select(projectId);
      cy.get('#root_category').select('soft_and_lic');
      cy.get('#root_purpose')
        .clear()
        .type(
          'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights. This is now more than 250 characters'
        );
      cy.get('#root_criticality').select('High');
      cy.get('#root_period').clear().type('25-11-2025');
      cy.get('body').click();
      cy.get('#root_vendor').clear().type('Microsoft');
      cy.get('#root_payment_method').select('Reimbursement');
      /* cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains('Task: Enter NDR Items', { timeout: 60000 });
*/
      // item 0
      cy.get('#root_item_0_sub_category').select('op_src');
      cy.get('#root_item_0_item_name')
        .clear()
        .type(
          'Open source software is code that is designed to be publicly accessible anyone can see, modify, END. This is now more than 100 characters'
        );
      cy.get('#root_item_0_qty').clear().type('2');
      cy.get('#root_item_0_currency_type').select('Crypto');
      cy.get('#root_item_0_currency').select('SNT');
      cy.get('#root_item_0_unit_price').type('1915');

      cy.get('#root_item > div:nth-child(3) > p > button').click();

      // item 1
      cy.get('#root_item_1_sub_category').select('lic_and_sub');
      cy.get('#root_item_1_item_name')
        .clear()
        .type(
          'A software license is a document that provides legally binding guidelines for the use and distri END.'
        );
      cy.get('#root_item_1_qty').clear().type('1');
      cy.get('#root_item_1_currency_type').select('Fiat');
      cy.get('#root_item_1_currency').select('AED');
      cy.get('#root_item_1_unit_price').type('4500');

      cy.get('button')
        .contains(/^Submit$/)
        .click();

      cy.contains('must NOT have more than 250 characters');
      cy.contains('Name must NOT have more than 100 characters');

      cy.get('#root_purpose')
        .clear()
        .type(
          'A software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights.'
        );

      cy.get('#root_item_0_item_name')
        .clear()
        .type(
          'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
        );
      cy.get('#root_item_1_item_name')
        .clear()
        .type(
          'A software license is a document that provides legally binding guidelines for the use and distri END'
        );

      cy.get('button')
        .contains(/^Submit$/)
        .click();
      cy.wait(6000);

      cy.contains(
        'Review and provide any supporting information or files for your request.',
        { timeout: 60000 }
      );

      cy.get('.cds--text-area__wrapper')
        .find('#root')
        .type(
          'test 2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows. This is now more than 250 characters.'
        );

      cy.get('button')
        .contains(/^Submit$/)
        .click();
      cy.wait(2000);

      cy.contains('must NOT have more than 250 characters');
      cy.get('.cds--text-area__wrapper')
        .find('#root')
        .clear()
        .type(
          '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta accessosar Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows.'
        );

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
    });
  });

});

// Software and License - With Files
describe('Initiate a Request - With Files', () => {
  Cypress._.times(1, () => {
    // Submit a Software and License request - Without Files
    it('13.Submit a Software and License request  - With Files', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('15-11-2035');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft Corp');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is developed in a decentralized and collaborative way'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('JPY');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('INR');
        cy.get('#root_item_1_unit_price').type('4500');

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
            'Open source software is developed in a decentralized and collaborative way, relying on peer review and community production. Open source software is often cheaper more flexible. \nhttps://www.redhat.com/en'
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

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);
      });
    });

    // Submit a Software and License request - With Files and Multiple items
    it('14.Submit a Software and License request - With Files and Multiple items', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Software licenses typically are proprietary, free or open source. The distinguishing feature is the terms under which users may redistribute or copy the software for future development or use.'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Meta Corp');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */

        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Definition. Open source software (OSS) is software that is distributed with its source code'
          );
        cy.get('#root_item_0_qty').clear().type('1');
        cy.get('#root_item_0_currency_type').select('Fiat');
        cy.get('#root_item_0_currency').select('AUD');
        cy.get('#root_item_0_unit_price').type('2416');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides binding guidelines for the use and distribution.'
          );
        cy.get('#root_item_1_qty').clear().type('5');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('EUR');
        cy.get('#root_item_1_unit_price').type('250');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 2
        cy.get('#root_item_2_sub_category').select('lic_and_sub');
        cy.get('#root_item_2_item_name')
          .clear()
          .type(
            'Subscription relates to a licensing model that allows users to pay regularly for a computer program'
          );
        cy.get('#root_item_2_qty').clear().type('10');
        cy.get('#root_item_2_currency_type').select('Crypto');
        cy.get('#root_item_2_currency').select('DAI');
        cy.get('#root_item_2_unit_price').type('12500');

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
            'A software license is a legal instrument (usually by way of contract law, with or without printed material) governing the use or redistribution of software. Under United States copyright law, all software is copyright protected.'
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

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
        cy.wait(2000);
      });
    });

    // Edit a Software and License request - With Files
    it('15.Edit a Software and License request  - With Files', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915.2456');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
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

        // cy.contains('Edit the Request').click();

        // cy.get('input[value="Edit the Request"]').click();

        cy.get('button')
          .contains(/^Edit Request$/)
          .click();

        // Form 1
        cy.contains('Task: Submit Details', { timeout: 60000 });

        cy.contains('Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
        cy.contains('High');
        cy.contains('25-11-2025');
        cy.contains('Microsoft');
        cy.contains('Reimbursement');
        cy.contains('Open source software is code that is designed to be publicly accessible anyone can see, modify, END');
        cy.contains('2');
        cy.contains('Crypto');
        cy.contains('SNT');
        cy.contains('1915.2456');
        cy.contains('A software license is a document that provides legally binding guidelines for the use and distri END');
        cy.contains('1');
        cy.contains('Fiat');
        cy.contains('AED');
        cy.contains('4500');

        cy.wait(2000);
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


        cy.contains('2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S,\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows', { timeout: 1000 });
        cy.contains('lorem-ipsum.pdf');
        cy.contains('png-5mb-1.png');
        cy.contains('Free_Test_Data_1MB_PDF.pdf');
        cy.contains('png-5mb-2.png');

        cy.get('.cds--text-area__wrapper')
          .find('#root')
          .type(
            'EDITING INFO : 2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
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
      });
    });

    // Save and Close a Software and License request 1 - With Files
    it('16.Save and Close a Software and License request 1 - With Files', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
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

        cy.wait(2000);

        cy.get('button')
          .contains(/^Save and Close$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Started by me', { timeout: 60000 });
        cy.logout();
      });
    });

    // Cancel a Software and License request - With Files
    it('17.Cancel a Software and License request  - With Files', () => {
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

      cy.url().then((currentUrl) => {
        // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
        // extract the digits after /tasks
        const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
        cy.log('==###############===processInstanceId : ', processInstanceId);
        const projectId = Cypress.env('project_id');
        cy.wait(2000);
        cy.get('#root_project').select(projectId);
        cy.get('#root_category').select('soft_and_lic');
        cy.get('#root_purpose')
          .clear()
          .type(
            'Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights'
          );
        cy.get('#root_criticality').select('High');
        cy.get('#root_period').clear().type('25-11-2025');
        cy.get('body').click();
        cy.get('#root_vendor').clear().type('Microsoft');
        cy.get('#root_payment_method').select('Reimbursement');
        /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
        // item 0
        cy.get('#root_item_0_sub_category').select('op_src');
        cy.get('#root_item_0_item_name')
          .clear()
          .type(
            'Open source software is code that is designed to be publicly accessible anyone can see, modify, END'
          );
        cy.get('#root_item_0_qty').clear().type('2');
        cy.get('#root_item_0_currency_type').select('Crypto');
        cy.get('#root_item_0_currency').select('SNT');
        cy.get('#root_item_0_unit_price').type('1915');

        cy.get('#root_item > div:nth-child(3) > p > button').click();

        // item 1
        cy.get('#root_item_1_sub_category').select('lic_and_sub');
        cy.get('#root_item_1_item_name')
          .clear()
          .type(
            'A software license is a document that provides legally binding guidelines for the use and distri END'
          );
        cy.get('#root_item_1_qty').clear().type('1');
        cy.get('#root_item_1_currency_type').select('Fiat');
        cy.get('#root_item_1_currency').select('AED');
        cy.get('#root_item_1_unit_price').type('4500');

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
            '2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows'
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

        // cy.contains('Cancel the Request').click();

        // cy.get('input[value="Cancel the Request"]').click();

        cy.get('button')
          .contains(/^Submit$/)
          .click();

        cy.wait(6000);
        /*cy.get('button')
          .contains(/^Return to Home$/)
          .click();*/

        cy.contains('Process Instance Id:', { timeout: 60000 });
        cy.logout();
      });
    });
  });
});
