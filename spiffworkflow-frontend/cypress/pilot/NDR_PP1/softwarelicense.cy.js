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
        cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' needs additional info. A software license is a document that provides legally binding guidelines for the use and distribution of software.Software licenses typically provide end users with the right to END.'));
        //cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' needs additional info.'));
    } else if (approvaltype === "cpapproved") {
        cy.get('#root > label:nth-child(3)').click();
        cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' is selecting CP is Approved.'));
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

        cy.get('.cds--text-area__wrapper').find('#root').clear().type('Providing additional info. Open source is a term that originally referred to open source software (OSS). Open source software is code that is designed to be publicly accessible—anyone can see, modify, and distribute.');

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

//Software and Licenses Path - Without Files
describe('Software and Licenses Path - Without Files', () => {

    Cypress._.times(1, () => {

        //Everyone approves with CP
        it('Everyone approves with CP', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
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
                //item 0
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Open source software is code that is designed to be publicly accessible anyone can see, modify, END');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('SNT');
                cy.get('#root_item_0_unit_price').type('1915');


                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('lic_and_sub');
                cy.get('#root_item_1_item_name').clear().type('A software license is a document that provides legally binding guidelines for the use and distri END');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('2021 Newest HP 17.3 inch FHD Laptop, AMD Ryzen 5 5500U 6core(Beat i7-1160G7, up to 4.0GHz),16GB RAM, 1TB PCIe SSD, Bluetooth 4.2, WiFi, HDMI, USB-A&C, Windows 10 S, w/Ghost Manta Accessories, Silver\nhttps://www.amazon.com/HP-i7-11G7-Bluetooth-Windows');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

            });
        });

        //Everyone approves the request
        it('Everyone approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Software licenses typically are proprietary, free or open source. The distinguishing feature is the terms under which users may redistribute or copy the software for future development or use.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('05-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Red Hat');
                cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */

                //item 0
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Open source has become a movement and a way of working that reaches beyond software production');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('NZD');
                cy.get('#root_item_0_unit_price').type('2416');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('lic_and_sub');
                cy.get('#root_item_1_item_name').clear().type('A software license is a document that states the rights of the developer and user of software.');
                cy.get('#root_item_1_qty').clear().type('1');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('STN');
                cy.get('#root_item_1_unit_price').type('380');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('Software also comes with a license key or product key. The key is used to identify and verify the specific version of the software. It is also used to activate the software device.\nhttps://www.techtarget.com/searchcio/definition/software-license');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );
                
                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    'Task: Update Application Landscape',
                    "approve"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('24-02-2026');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Oracle');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('It defines the terms of. A user must agree to the terms of the license when acquiring the software.');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('Software also comes with a license key or product key. The key is used to identify and verify the specific version of the software. It is also used to activate the software device.\nhttps://www.techtarget.com/searchcio/definition/software-license');

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
                cy.wait(2000);

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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('A software license establishes the rights of all parties involved with the software: the author, the provider and the end users. It defines the relationship between the software company and users and explains how they are protected');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('25-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('ABC Licensing Co');
                cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('They protect developers\' intellectual property and trade secrets based on copyright laws');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('They define what users can do with software code they did not write.');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );


            });
        });

        //Infra reject the request
        it('Infra rejects', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('There are two general types of software licenses that differ based on how they are viewed under copyright law.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('02-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Meta');
                cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('The open source movement uses the values and decentralized production model of open source software');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('Free and open source software (FOSS) licenses are often referred to as open source. FOSS source code is available to the customer along with the software product. The customer is usually allowed to use the source code to change the software.');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    null,
                    "reject"
                );

            });
        });


    });
});

//Software and Licenses Path - Without Files and with only mandatory fields
describe('Software and Licenses Path -  Without Files and with only mandatory fields', () => {

    Cypress._.times(1, () => {

        //Everyone approves with CP
        it('Everyone approves with CP', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Need to buy a Software');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('24-11-2025');
                cy.get('body').click();
                //cy.get('#root_vendor').clear().type('Embassar');
                //cy.get('#root_payment_method').select('Reimbursement');
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

                //cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

            });
        });

        //Everyone approves the request
        it('Everyone approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('need software');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('20-11-2025');
                cy.get('body').click();
                //cy.get('#root_vendor').clear().type('Embassar');
                //cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('open source');
                cy.get('#root_item_0_qty').clear().type('1');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('AED');
                cy.get('#root_item_0_unit_price').type('1520');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                //cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    'Task: Update Application Landscape',
                    "approve"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Nee license');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('20-02-2026');
                cy.get('body').click();
                //cy.get('#root_vendor').clear().type('Subsc LTD');
                //cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('Software development');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('EUR');
                cy.get('#root_item_0_unit_price').type('1400');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                //cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

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
                cy.wait(2000);

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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Software needed');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('05-02-2025');
                cy.get('body').click();
                //cy.get('#root_vendor').clear().type('ABC Licensing Co');
                //cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('License');
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

                //cy.get('.cds--text-area__wrapper').find('#root').type('It\’s free and easy to post a job. Simply fill in a title, description and budget and competitive bids come within minutes. No job is too big or too small. We\'ve got freelancers for jobs of any size or budget across 1800 skills. No job is too complex.');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );


            });
        });

        //Infra reject the request
        it('Infra rejects', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Software is needed');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('25-11-2025');
                cy.get('body').click();
                // cy.get('#root_vendor').clear().type('Embassar');
                // cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Open source');
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

                //cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, ‘consultant’ and advisor’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    null,
                    "reject"
                );

            });
        });


    });
});

//Software and Licenses Path - With Files
describe('Software and Licenses Path - With Files', () => {

    Cypress._.times(1, () => {

        //Everyone approves with CP
        it('Everyone approves with CP', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Sware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
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
                //item 0
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Open source software is developed in a decentralized and collaborative way');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('JPY');
                cy.get('#root_item_0_unit_price').type('2416');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('lic_and_sub');
                cy.get('#root_item_1_item_name').clear().type('A software license is a document that provides legally binding guidelines for the use and distri END');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('Open source software is developed in a decentralized and collaborative way, relying on peer review and community production. Open source software is often cheaper more flexible. \nhttps://www.redhat.com/en');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

            });
        });

        //Everyone approves the request
        it('Everyone approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Stware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('30-11-2024');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('ORACLE LTD');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('A bounty is a payment or reward of money to locate');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('SGD');
                cy.get('#root_item_0_unit_price').type('2416');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('Open source software is developed in a decentralized and collaborative way, relying on peer review and community production. Open source software is often cheaper more flexible. \nhttps://www.redhat.com/en');

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
                    .attachFile(['png-5mb-2.png']);

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    'Task: Update Application Landscape',
                    "approve"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Stware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('24-12-2023');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Subscription PVT');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('Software development consultants with Python background');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('Open source software is developed in a decentralized and collaborative way, relying on peer review and community production. Open source software is often cheaper more flexible. \nhttps://www.redhat.com/en');

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
                    .attachFile(['png-5mb-2.png']);

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
                cy.wait(2000);

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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Stware\nA software license is a document that provides legally binding guidelines for the use and distribution of software.\nSoftware licenses typically provide end users with the right to one or more copies of the software without violating copyrights');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('25-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('LIC INST');
                cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('Freelancers to do the Python development and front end react app development');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('A software license is a legal instrument (usually by way of contract law, with or without printed material) governing the use or redistribution of software. Under United States copyright law, all software is copyright protected.');

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
                    .attachFile(['png-5mb-2.png']);

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );



            });
        });

        //Infra rejects the request
        it('Infra Rejects', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Proprietary licenses are often referred to as closed source. They provide customers with operational code. Users cannot freely alter this software. These licenses also usually restrict reverse engineering the software\'s code to obtain the source code');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('25-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Red HAT');
                cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('They provide customers with operational code. Users cannot freely alter this software.');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('STN');
                cy.get('#root_item_0_unit_price').type('2416');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('Free and open source software (FOSS) licenses are often referred to as open source. FOSS source code is available to the customer along with the software product. The customer is usually allowed to use the source code to change the software.');

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
                    .attachFile(['png-5mb-2.png']);

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    null,
                    "reject"
                );

            });
        });

    });
});

//Software and Licenses Path - With Files and Multiple items
describe('Software and Licenses Path - With Files and Multiple items', () => {

    Cypress._.times(1, () => {

        //Everyone approves with CP
        it('Everyone approves with CP', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Software licenses typically are proprietary, free or open source. The distinguishing feature is the terms under which users may redistribute or copy the software for future development or use.');
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

                //item 0
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Definition. Open source software (OSS) is software that is distributed with its source code');
                cy.get('#root_item_0_qty').clear().type('1');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('AUD');
                cy.get('#root_item_0_unit_price').type('2416');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('lic_and_sub');
                cy.get('#root_item_1_item_name').clear().type('A software license is a document that provides binding guidelines for the use and distribution.');
                cy.get('#root_item_1_qty').clear().type('5');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('EUR');
                cy.get('#root_item_1_unit_price').type('250');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('lic_and_sub');
                cy.get('#root_item_2_item_name').clear().type('Subscription relates to a licensing model that allows users to pay regularly for a computer program');
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

                cy.get('.cds--text-area__wrapper').find('#root').type('A software license is a legal instrument (usually by way of contract law, with or without printed material) governing the use or redistribution of software. Under United States copyright law, all software is copyright protected.');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

            });
        });

        //Everyone approves the request
        it('Everyone approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Software licenses typically are proprietary, free or open source. The distinguishing feature is the terms under which users may redistribute or copy the software for future development or use.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('25-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Apple');
                cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                //item 0
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Definition. Open source software (OSS) is software that is distributed with its source code');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('AED');
                cy.get('#root_item_0_unit_price').type('1250');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('lic_and_sub');
                cy.get('#root_item_1_item_name').clear().type('A software license is a document that provides binding guidelines for the use and distribution.');
                cy.get('#root_item_1_qty').clear().type('5');
                cy.get('#root_item_1_currency_type').select('Crypto');
                cy.get('#root_item_1_currency').select('SNT');
                cy.get('#root_item_1_unit_price').type('25000');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('lic_and_sub');
                cy.get('#root_item_2_item_name').clear().type('Subscription relates to a licensing model that allows users to pay regularly for a computer program');
                cy.get('#root_item_2_qty').clear().type('3');
                cy.get('#root_item_2_currency_type').select('Crypto');
                cy.get('#root_item_2_currency').select('ETH');
                cy.get('#root_item_2_unit_price').type('2.10');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('A software license is a legal instrument (usually by way of contract law, with or without printed material) governing the use or redistribution of software. Under United States copyright law, \nhttps://en.wikipedia.org/wiki/Software_license');


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
                    .attachFile(['png-5mb-2.png']);

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    'Task: Update Application Landscape',
                    "approve"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Software licenses typically are proprietary, free or open source. The distinguishing feature is the terms under which users may redistribute or copy the software for future development or use.');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('24-02-2026');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Subscription PVT');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */

                //item 0
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('Subscription relates to a licensing model that allows users to pay regularly for a computer program');
                cy.get('#root_item_0_qty').clear().type('5');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('USD');
                cy.get('#root_item_0_unit_price').type('250.50');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('lic_and_sub');
                cy.get('#root_item_1_item_name').clear().type('A software license is a document that provides binding guidelines for the use and distribution.');
                cy.get('#root_item_1_qty').clear().type('5');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('GBP');
                cy.get('#root_item_1_unit_price').type('5200');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('op_src');
                cy.get('#root_item_2_item_name').clear().type('Definition. Open source software (OSS) is software that is distributed with its source code');
                cy.get('#root_item_2_qty').clear().type('3');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('HKD');
                cy.get('#root_item_2_unit_price').type('2100');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('A software license is a legal instrument (usually by way of contract law, with or without printed material) governing the use or redistribution of software. Under United States copyright law, \nhttps://en.wikipedia.org/wiki/Software_license');

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
                cy.wait(2000);

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

            /*            cy.contains('Please select the type of request to start the process.');
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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Free and open source software (FOSS) licenses are often referred to as open source. FOSS source code is available to the customer along with the software product. The customer is usually allowed to use the source code to change the software.');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('25-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('LIC INST');
                cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                //item 0
                cy.get('#root_item_0_sub_category').select('lic_and_sub');
                cy.get('#root_item_0_item_name').clear().type('A software license is a document that provides binding guidelines for the use and distribution.');
                cy.get('#root_item_0_qty').clear().type('24');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('SNT');
                cy.get('#root_item_0_unit_price').type('450');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('op_src');
                cy.get('#root_item_1_item_name').clear().type('Definition. Open source software (OSS) is software that is distributed with its source code');
                cy.get('#root_item_1_qty').clear().type('15');
                cy.get('#root_item_1_currency_type').select('Crypto');
                cy.get('#root_item_1_currency').select('ETH');
                cy.get('#root_item_1_unit_price').type('0.85');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('lic_and_sub');
                cy.get('#root_item_2_item_name').clear().type('Subscription relates to a licensing model that allows users to pay regularly for a computer program');
                cy.get('#root_item_2_qty').clear().type('8');
                cy.get('#root_item_2_currency_type').select('Crypto');
                cy.get('#root_item_2_currency').select('DAI');
                cy.get('#root_item_2_unit_price').type('2100');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('A software license is a legal instrument (usually by way of contract law, with or without printed material) governing the use or redistribution of software. Under United States copyright law, \nhttps://en.wikipedia.org/wiki/Software_license');

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "cpapproved"
                );

                submitWithUser(
                    legalsmeUsername,
                    legalsmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );



            });
        });

        //Infra rejects the request
        it('Infra Rejects', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Request Goods or Services');

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
                cy.get('#root_category').select('soft_and_lic');
                cy.get('#root_purpose').clear().type('Free and open source software (FOSS) licenses are often referred to as open source. FOSS source code is available to the customer along with the software product. The customer is usually allowed to use the source code to change the software.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('20-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Atlassian');
                cy.get('#root_payment_method').select('Debit Card');
                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                //item 0
                cy.contains('Task: Enter NDR Items', { timeout: 60000 });
                cy.get('#root_item_0_sub_category').select('op_src');
                cy.get('#root_item_0_item_name').clear().type('Definition. Open source software (OSS) is software that is distributed with its source code');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('THB');
                cy.get('#root_item_0_unit_price').type('1350');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('op_src');
                cy.get('#root_item_1_item_name').clear().type('Open source software (OSS) is software that is distributed with its source code');
                cy.get('#root_item_1_qty').clear().type('15');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('TRY');
                cy.get('#root_item_1_unit_price').type('3200');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('lic_and_sub');
                cy.get('#root_item_2_item_name').clear().type('Subscription relates to a licensing model that allows users to pay regularly for a computer program');
                cy.get('#root_item_2_qty').clear().type('8');
                cy.get('#root_item_2_currency_type').select('Crypto');
                cy.get('#root_item_2_currency').select('DAI');
                cy.get('#root_item_2_unit_price').type('2100');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('A typical software license grants the licensee, typically an end-user, permission to use one or more copies of software in ways where such a use would otherwise potentially constitute copyright.\nhttps://en.wikipedia.org/wiki/Software_license');


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
                    .attachFile(['png-5mb-2.png']);

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
                cy.wait(2000);

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

                let ppgbasmeUsername = Cypress.env('ppgbasme_username');
                let ppgbasmePassword = Cypress.env('ppgbasme_password');
                let securitysmeUsername = Cypress.env('securitysme_username');
                let securitysmePassword = Cypress.env('securitysme_password');
                let infrasmeUsername = Cypress.env('infrasme_username');
                let infrasmePassword = Cypress.env('infrasme_password');
                let legalsmeUsername = Cypress.env('legalsme_username');
                let legalsmePassword = Cypress.env('legalsme_password');

                submitWithUser(
                    ppgbasmeUsername,
                    ppgbasmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    securitysmeUsername,
                    securitysmePassword,
                    processInstanceId,
                    null,
                    "approve"
                );

                submitWithUser(
                    infrasmeUsername,
                    infrasmePassword,
                    processInstanceId,
                    null,
                    "reject"
                );

            });
        });

    });
});

