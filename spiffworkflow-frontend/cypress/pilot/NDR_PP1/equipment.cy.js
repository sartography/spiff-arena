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
        cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' needs additional info. By contrast, software is the set of instructions that can be stored and run by hardware. Hardware is so-termed because it is "hard" or rigid with respect to changes, whereas software is "soft" END.'));
    } else if (approvaltype === "escalateBO") {
        cy.get('#root > label:nth-child(1)').click();
        cy.get('.field-boolean > label:nth-child(1)').click();
        cy.get('.cds--text-area__wrapper').find('#root').type(username.concat(' is escalating to Budget owner.'));
    } else if (approvaltype === "providemoreinfo") {
        //Form 1
        cy.contains('Task: Submit Details', { timeout: 60000 });
        cy.get('button')
            .contains(/^Submit$/)
            .click();
        //Form 2      
        /* cy.contains('Task: Enter NDR Items', { timeout: 60000 });
         cy.get('button')
             .contains(/^Submit$/)
             .click();*/
        //Form 3
        cy.contains(
            'Task: Review the Request',
            { timeout: 60000 });

        cy.get('.cds--text-area__wrapper').find('#root').clear().type('Providing additional info. Computer hardware includes the physical parts of a computer, such as the case, central processing unit (CPU), random access memory (RAM), monitor, mouse, keyboard, computer data storage, graphics card, sound card');

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

//Equipment Path - Without Files
describe.only('Equipment Path - Without Files', () => {

    Cypress._.times(1, () => {
        //Out of Policy. People Ops Partner Group and Budget owner approves the request
        it('Out of Policy. People Ops Partner Group and Budget owner approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('By contrast, software is the set of instructions that can be stored and run by hardware. Hardware is so-termed because it is "hard" or rigid with respect to changes, whereas software is "soft" because it is easy to change..');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('25-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Mech Tech');
                cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                //item 0
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Hardware is typically directed by the software to execute any command or instruction');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('AUD');
                cy.get('#root_item_0_unit_price').type('5000');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('ledger');
                cy.get('#root_item_1_item_name').clear().type('A mainframe computer is a much larger computer that typically fills a room and may cost many hundred');
                cy.get('#root_item_1_qty').clear().type('1');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CAD');
                cy.get('#root_item_1_unit_price').type('1355');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('yubikey');
                cy.get('#root_item_2_item_name').clear().type('A supercomputer is superficially similar to a mainframe but is instead intended for extremely demand');
                cy.get('#root_item_2_qty').clear().type('6');
                cy.get('#root_item_2_currency_type').select('Crypto');
                cy.get('#root_item_2_currency').select('ETH');
                cy.get('#root_item_2_unit_price').type('2.34');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 3
                cy.get('#root_item_3_sub_category').select('mic_and_head');
                cy.get('#root_item_3_item_name').clear().type('The term supercomputer does not refer to a specific technology.');
                cy.get('#root_item_3_qty').clear().type('6');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('SNT');
                cy.get('#root_item_3_unit_price').type('2300');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann. This describes a design architecture for a electronic digital computer with subdivisions of a processing unit');

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
                cy.log('=====after logout ---');


                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

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

        //Out of Policy. People Ops Partner Group approves and Budget owner rejects the request
        it('Out of Policy. People Ops Partner Group approves and Budget owner rejects ', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Electronic appliances and services related to the personal computer, including the PC (desktop or laptop), and communication between computers and the services required by intercommunication networks. These fundamentally include');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('24-02-2026');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('BestBUY');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                //item 0
                cy.get('#root_item_0_sub_category').select('yubikey');
                cy.get('#root_item_0_item_name').clear().type('Output devices are designed around the senses of human beings. For example, monitors display text');
                cy.get('#root_item_0_qty').clear().type('5');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('EUR');
                cy.get('#root_item_0_unit_price').type('3200');



                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('When using computer hardware, an upgrade means adding new or additional hardware to a computer that improves its performance, increases its capacity, or adds new features. For example, \nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

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

        //Out of Policy. People Ops Partner Group approves and Budget owner request for additional details
        it('Out of Policy. People Ops Partner Group approves and Budget owner needs more info', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Computer hardware includes the physical parts of a computer, such as the case, central processing unit (CPU), random access memory (RAM), monitor, mouse, keyboard, computer data storage, graphics card, sound card, speakers and motherboard.[1][2]');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('25-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Amazon.com');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Rather it indicates the fastest computations available at any given time. In mid-2011, the fastest');
                cy.get('#root_item_0_qty').clear().type('4');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('USD');
                cy.get('#root_item_0_unit_price').type('4000');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('A supercomputer is superficially similar to a mainframe but is instead intended for extremely demanding computational tasks. As of November 2021, the fastest supercomputer on the TOP500 supercomputer list is Fugaku, in Japan');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

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

                // people ops approves second time
                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
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

        //Within Policy. People Ops Partner Group approves the request
        it('Within Policy. People Ops Partner Group approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('By contrast, software is the set of instructions that can be stored and run by hardware. Hardware is so-termed because it is "hard" or rigid with respect to changes, whereas software is "soft" because it is easy to change.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('15-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('EBAY');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Because computer parts contain hazardous materials, there is a growing movement to recycle ');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('HKD');
                cy.get('#root_item_0_unit_price').type('1236');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('Computer hardware contain dangerous chemicals such as lead, mercury, nickel, and cadmium. According to the EPA these e-wastes have a harmful effect on the environment unless they are disposed properly. \nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

            });
        });

        //Within Policy. People Ops Partner Group rejects the request
        it('Within Policy. People Ops Partner Group rejects', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann. This describes a design architecture for a electronic digital computer with subdivisions of a processing unit');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('05-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Best Buy');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Computer components contain many toxic substances, like dioxins, polychlorinated biphenyls (PCBs)');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('AED');
                cy.get('#root_item_0_unit_price').type('320');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('For professionals working in the professional services, \‘consultant\’ and advisor\’ are often used and fall under common terminology. Consultancy.uk zooms in on this field to get a closer look. \n https://www.consultancy.uk/career/what-is-consulting');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "reject"
                );

            });
        });

        //Within Policy. People Ops Partner Group request additional info
        it('Within Policy. People Ops Partner Group needs more info', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case. The computer case holds the motherboard');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('05-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Walmart');
                cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('As computer hardware contain a wide number of metals inside, the United States Environmental');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('CAD');
                cy.get('#root_item_0_unit_price').type('435');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann. \nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
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

                //peopleops approves second time
                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );


            });
        });
        //Within Policy. People Ops Partner Group and Budget owner approves the request
        it('Within Policy. People Ops Partner Group and Budget owner approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Laptops are designed for portability but operate similarly to desktop PCs.[5] They may use lower-power or reduced size components, with lower performance than a similarly priced desktop computer');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('25-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Fry\'s');
                cy.get('#root_payment_method').select('Crypto Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Recycling a computer is made easier by a few of the national services, such as Dell and Apple.');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('USD');
                cy.get('#root_item_0_unit_price').type('1200');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann. \nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
                );

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

        //Within Policy. People Ops Partner Group approves and Budget owner rejects the request
        it('Within Policy. People Ops Partner Group approves and Budget owner rejects ', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('The computer case encloses most of the components of the system. It provides mechanical support and protection for internal elements such as the motherboard, disk drives, and power supplies, and controls and directs the flow of cooling air over int. ');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('14-02-2026');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('BestBUY');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Because computer parts contain hazardous materials, there is a growing movement to recycle old');
                cy.get('#root_item_0_qty').clear().type('5');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('EUR');
                cy.get('#root_item_0_unit_price').type('300');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
                );

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

        //Within Policy. People Ops Partner Group approves and Budget owner request for additional details
        it('Within Policy. People Ops Partner Group approves and Budget owner needs more info', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('The motherboard is the main component of a computer. It is a board with integrated circuitry that connects the other parts of the computer including the CPU, the RAM, the disk drives (CD, DVD, hard disk, or any others) as well as any peripherals');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('15-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Amazon.com');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Recycling a computer is made easier by a few of the national services, such as Dell and Apple.');
                cy.get('#root_item_0_qty').clear().type('4');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('USD');
                cy.get('#root_item_0_unit_price').type('400');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
                );

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

                //people ops approves second time
                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );


            });
        });

    });
});

//Equipment Path - With Files
describe('Equipment Path - With Files', () => {

    Cypress._.times(1, () => {
        //Out of Policy. People Ops Partner Group and Budget owner approves the request
        it('Out of Policy. People Ops Partner Group and Budget owner approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Equipment most commonly refers to a set of tools or other objects commonly used to achieve a particular objective. Different jobs require different kinds of equipment.\nhttps://en.wikipedia.org/wiki/Equipment');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('15-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Mech Tech');
                cy.get('#root_payment_method').select('Debit Card');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                //item 0
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('When using computer hardware, an upgrade means adding new or additional hardware to a computer that');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('AUD');
                cy.get('#root_item_0_unit_price').type('12300');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 1
                cy.get('#root_item_1_sub_category').select('ledger');
                cy.get('#root_item_1_item_name').clear().type('A mainframe computer is a much larger computer that typically fills a room and may cost many hundred');
                cy.get('#root_item_1_qty').clear().type('1');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CAD');
                cy.get('#root_item_1_unit_price').type('1355');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 2
                cy.get('#root_item_2_sub_category').select('yubikey');
                cy.get('#root_item_2_item_name').clear().type('A supercomputer is superficially similar to a mainframe but is instead intended for extremely demand');
                cy.get('#root_item_2_qty').clear().type('6');
                cy.get('#root_item_2_currency_type').select('Crypto');
                cy.get('#root_item_2_currency').select('ETH');
                cy.get('#root_item_2_unit_price').type('2.10');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                //item 3
                cy.get('#root_item_3_sub_category').select('mic_and_head');
                cy.get('#root_item_3_item_name').clear().type('The term supercomputer does not refer to a specific technology.');
                cy.get('#root_item_3_qty').clear().type('6');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('SNT');
                cy.get('#root_item_3_unit_price').type('2300');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

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

        //Out of Policy. People Ops Partner Group approves and Budget owner rejects the request
        it('Out of Policy. People Ops Partner Group approves and Budget owner rejects ', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('The motherboard is the main component of a computer. It is a board with integrated circuitry that connects the other parts of the computer including the CPU, the RAM, the disk drives (CD, DVD, hard disk, or any others) as well as any peripherals');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('24-02-2026');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('BestBUY');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Because computer parts contain hazardous materials, there is a growing movement to recycle old');
                cy.get('#root_item_0_qty').clear().type('5');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('EUR');
                cy.get('#root_item_0_unit_price').type('3000');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

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

        //Out of Policy. People Ops Partner Group approves and Budget owner request for additional details
        it('Out of Policy. People Ops Partner Group approves and Budget owner needs more info', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('The CPU (central processing unit), which performs most of the calculations which enable a computer to function, and is referred to as the brain of the computer.\nhttps://en.wikipedia.org/wiki/Computer_hardware');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('05-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Amazon.com');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Because computer parts contain hazardous materials, there is a growing movement to recycle old');
                cy.get('#root_item_0_qty').clear().type('4');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('USD');
                cy.get('#root_item_0_unit_price').type('4000');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');
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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

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

                //people ops approves second time
                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
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

        //Within Policy. People Ops Partner Group approves the request
        it('Within Policy. People Ops Partner Group approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('An expansion card in computing is a printed circuit board that can be inserted into an expansion slot of a computer motherboard or backplane to add functionality to a computer system via the expansion bus. Expansion cards can be used to obtain');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('15-11-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Amazon');
                cy.get('#root_payment_method').select('Debit Card');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Recycling a computer is made easier by a few of the national services, such as Dell and Apple.');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('CHF');
                cy.get('#root_item_0_unit_price').type('240');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );

            });
        });

        //Within Policy. People Ops Partner Group rejects the request
        it('Within Policy. People Ops Partner Group rejects', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Storage device is any computing hardware and digital media that is used for storing, porting and extracting data files and objects. It can hold and store information both temporarily and permanently and can be internal or external to a computer.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('29-11-2023');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Best Buy');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('ledger');
                cy.get('#root_item_0_item_name').clear().type('The central processing unit contains many toxic materials. It contains lead and chromium in metal');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('CNY');
                cy.get('#root_item_0_unit_price').type('1560');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann..\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "reject"
                );

            });
        });

        //Within Policy. People Ops Partner Group request additional info
        it('Within Policy. People Ops Partner Group needs more info', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Data is stored by a computer using a variety of media. Hard disk drives (HDDs) are found in virtually all older computers, due to their high capacity and low cost, but solid-state drives (SSDs) are faster and more power efficient.');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('12-11-2024');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Fry\'s');
                cy.get('#root_payment_method').select('Debit Card');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('yubikey');
                cy.get('#root_item_0_item_name').clear().type('Data is stored by a computer using a variety of media. Hard disk drives (HDDs) are found');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('COP');
                cy.get('#root_item_0_unit_price').type('1230');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann..\nhttps://en.wikipedia.org/wiki/Computer_hardware');
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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
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

                //people ops approves second time
                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "approve"
                );


            });
        });
        //Within Policy. People Ops Partner Group and Budget owner approves the request
        it('Within Policy. People Ops Partner Group and Budget owner approves', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('To transfer data between computers, an external flash memory device (such as a memory card or USB flash drive) or optical disc (such as a CD-ROM, DVD-ROM or BD-ROM) may be used. ');
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('15-12-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Amazon.com');
                cy.get('#root_payment_method').select('Reimbursement');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('mic_and_head');
                cy.get('#root_item_0_item_name').clear().type('Data is stored by a computer using a variety of media. Hard disk drives (HDDs) are found');
                cy.get('#root_item_0_qty').clear().type('2');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('ETB');
                cy.get('#root_item_0_unit_price').type('3200');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann..\nhttps://en.wikipedia.org/wiki/Computer_hardware');
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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
                );

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

        //Within Policy. People Ops Partner Group approves and Budget owner rejects the request
        it('Within Policy. People Ops Partner Group approves and Budget owner rejects ', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Input and output devices are typically housed externally to the main computer chassis. The following are either standard or very common to many computer systems.');
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('17-02-2026');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('BestBUY');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('mic_and_head');
                cy.get('#root_item_0_item_name').clear().type('The central processing unit contains many toxic materials. It contains lead and chromium in metal');
                cy.get('#root_item_0_qty').clear().type('5');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('EUR');
                cy.get('#root_item_0_unit_price').type('1');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The template for all modern computers is the Von Neumann architecture, detailed in a 1945 paper by Hungarian mathematician John von Neumann..\nhttps://en.wikipedia.org/wiki/Computer_hardware');
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

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
                );

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

        //Within Policy. People Ops Partner Group approves and Budget owner request for additional details
        it('Within Policy. People Ops Partner Group approves and Budget owner needs more info', () => {
            let username = Cypress.env('requestor_username');
            let password = Cypress.env('requestor_password');
            cy.log('=====username : ' + username);
            cy.log('=====password : ' + password);

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

            cy.contains(
                'Request Goods or Services',
                { timeout: 60000 }
            );

            //cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks
                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                let projectId = Cypress.env('project_id');
                cy.wait(2000);
                cy.get('#root_project').select(projectId);
                cy.get('#root_category').select('equip');
                cy.get('#root_purpose').clear().type('Input devices allow the user to enter information into the system, or control its operation. Most personal computers have a mouse and keyboard, but laptop systems typically use a touchpad instead of a mouse. Other input devices include webcams, mic');
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('16-02-2025');
                cy.get('body').click();
                cy.get('#root_vendor').clear().type('Amazon.com');
                cy.get('#root_payment_method').select('Bank Transfer');
                /* cy.get('button')
                     .contains(/^Submit$/)
                     .click();
 
                 cy.contains('Task: Enter NDR Items', { timeout: 60000 });
 */
                cy.get('#root_item_0_sub_category').select('laptops');
                cy.get('#root_item_0_item_name').clear().type('Because computer parts contain hazardous materials, there is a growing movement to recycle old');
                cy.get('#root_item_0_qty').clear().type('4');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('GBP');
                cy.get('#root_item_0_unit_price').type('420');


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Review and provide any supporting information or files for your request.',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper').find('#root').type('The personal computer is one of the most common types of computer due to its versatility and relatively low price. Desktop personal computers have a monitor, a keyboard, a mouse, and a computer case.\nhttps://en.wikipedia.org/wiki/Computer_hardware');

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

                cy.wait(20000);
                cy.get('button')
                    .contains(/^Return to Home$/)
                    .click();

                cy.contains('Started by me', { timeout: 60000 });
                cy.logout();
                cy.wait(2000);

                let peopleOpsUsername = Cypress.env('peopleopssme_username');
                let peopleOpsPassword = Cypress.env('peopleopssme_password');
                cy.log('=====peopleOpsUsername : ' + peopleOpsUsername);
                cy.log('=====peopleOpsPassword : ' + peopleOpsPassword);

                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
                );

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

                //people ops escalate to BO second time
                submitWithUser(
                    peopleOpsUsername,
                    peopleOpsPassword,
                    processInstanceId,
                    null,
                    "escalateBO"
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