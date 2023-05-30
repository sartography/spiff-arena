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
                "Providing additional info. It’s free and easy to post a job. Simply fill in a title, description and budget and competitive bids come within minutes. No job is too big or too small. We've got people for jobs of any size."
            );

        // cy.contains('Submit the Request').click();
        // cy.get('input[value="Submit the Request"]').click();
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

    cy.wait(5000);
    //cy.get('button').contains('Return to Home', { timeout: 60000 });
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

// Request Travel - Without Files
describe.only('Request Travel - Without Files', () => {
    Cypress._.times(1, () => {
        // Initiate request - Team Event - Without Files
        it('Initiate request - Team Event - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Before you start planning your trip, make sure to check your company’s rules, procedures, and do’s & don’ts when it comes to corporate travel. Here you’ll find more information about corporate travel policies, which include things such as where to ..'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('17-09-2028');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core1 Contributor');
                cy.get('#root_start_date').clear().type('14-09-2028');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('20-09-2028');
                cy.get('body').click();
                cy.get('#root_event_type').select('team_event');
                //cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Great Guac Off is one of the best team building events. Participants compete in teams to perfect it.');

                cy.get('#root_event_destination').clear('Tabaquite');
                cy.get('#root_event_destination').type('Tabaquite');
                cy.get('.cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('o');
                cy.get('#root_departure_from').type('o');
                cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('h');
                cy.get('#root_return_to').type('h');
                cy.get('#downshift-2-item-1 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Our staff can facilitate your accommodation needs from a range of Home-stay options and can also.'
                    );
                cy.get('#root_item_0_qty').clear().type('7');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('ETH');
                cy.get('#root_item_0_unit_price').type('1.15');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Now you have all you need for your seamless flight. With a variety of services such as Flexi Ticket.'
                    );
                cy.get('#root_item_1_qty').clear().type('5');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CAD');
                cy.get('#root_item_1_unit_price').type('2300');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        'Ensure a quality, cost effective and safe integrated transport system and services that will provi.'
                    );
                cy.get('#root_item_2_qty').clear().type('9');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('AUD');
                cy.get('#root_item_2_unit_price').type('1205.75');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 3
                cy.get('#root_item_3_sub_category').select('tickets');
                cy.get('#root_item_3_item_name')
                    .clear()
                    .type(
                        'Book Your Tickets In Advance And Get A Chance To Experience Unlimited Rides On 1 Day. Experience....'
                    );
                cy.get('#root_item_3_qty').clear().type('18');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('SNT');
                cy.get('#root_item_3_unit_price').type('430.50');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A host brings all the ingredients, leads groups through mini-games, and encourages participants to taunt or cheer. This cookless cook-off is available in various venues. https://teambuilding.com/blog/team-building-events'
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
                cy.wait(1000);
            });
        });
        // Initiate request - Conference - Without Files and with mandatory fields only
        it('Initiate request - Conference - Without Files and with mandatory fields only', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Before you start planning your trip, make sure to check your company’s rules, procedures, and do’s & don’ts when it comes to corporate travel. Here you’ll find more information about corporate travel policies, which include things such as where to ..'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('17-09-2028');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core1 Contributor');
                cy.get('#root_start_date').clear().type('14-09-2028');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('20-09-2028');
                cy.get('body').click();
                cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Great Guac Off is one of the best team building events. Participants compete in teams to perfect it.');

                cy.get('#root_event_destination').clear('y');
                cy.get('#root_event_destination').type('yellow');
                cy.get('#downshift-0-item-3 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('c');
                cy.get('#root_departure_from').type('colombo');
                cy.get('#downshift-1-item-1 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('s');
                cy.get('#root_return_to').type('spring');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Our staff can facilitate your accommodation needs from a range of Home-stay options and can also.'
                    );
                cy.get('#root_item_0_qty').clear().type('7');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('ETH');
                cy.get('#root_item_0_unit_price').type('1.15');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Now you have all you need for your seamless flight. With a variety of services such as Flexi Ticket.'
                    );
                cy.get('#root_item_1_qty').clear().type('5');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CAD');
                cy.get('#root_item_1_unit_price').type('2300');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        'Ensure a quality, cost effective and safe integrated transport system and services that will provi.'
                    );
                cy.get('#root_item_2_qty').clear().type('9');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('AUD');
                cy.get('#root_item_2_unit_price').type('1205.75');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 3
                cy.get('#root_item_3_sub_category').select('tickets');
                cy.get('#root_item_3_item_name')
                    .clear()
                    .type(
                        'Book Your Tickets In Advance And Get A Chance To Experience Unlimited Rides On 1 Day. Experience....'
                    );
                cy.get('#root_item_3_qty').clear().type('18');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('SNT');
                cy.get('#root_item_3_unit_price').type('430.50');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A host brings all the ingredients, leads groups through mini-games, and encourages participants to taunt or cheer. This cookless cook-off is available in various venues. https://teambuilding.com/blog/team-building-events'
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
                cy.wait(1000);
            });
        });
        // Edit request - Meetup - Without Files
        it('Edit request - Meetup - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Happy hours are a go-to team social event. These gatherings involve heading to a local watering hole, setting up a bar in the office, and socializing over drinks and snacks.'
                    );
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('27-02-2024');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core1 Contributor');
                cy.get('#root_start_date').clear().type('26-02-2024');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('04-03-2024');
                cy.get('body').click();
                cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('The most common times for happy hours -directly after work or during the final hours of the workday.');

                cy.get('#root_event_destination').clear('s');
                cy.get('#root_event_destination').type('sydney');
                cy.get('#downshift-0-item-2 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('o');
                cy.get('#root_departure_from').type('oslo');
                cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('ch');
                cy.get('#root_return_to').type('chica');
                cy.get('#downshift-2-item-1 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Entertainment ideas include answering icebreaker questions, playing pool or board games.'
                    );
                cy.get('#root_item_0_qty').clear().type('9');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('CHF');
                cy.get('#root_item_0_unit_price').type('140.65');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'You could assign a theme or leave the event more free-form encourage teammates to chat with peers.'
                    );
                cy.get('#root_item_1_qty').clear().type('4');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CNY');
                cy.get('#root_item_1_unit_price').type('5689');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A professional performer plays the role of host and leads teams in new takes on quiz games, like Majority Rules and Champion Challenge.'
                    );

                cy.get('button')
                    .contains(/^Edit Request$/)
                    .click();

                // Form 1
                cy.contains('Task: Submit Details', { timeout: 60000 });
                cy.wait(2000);
                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                // Form 2
                cy.contains('Task: Review the Request', { timeout: 60000 });

                cy.get('.cds--text-area__wrapper').find('#root').type('EDITING INFO');
            });
        });
        // Save and Close All fields Form 1 - All Hands - Without Files
        it('Save and Close All fields - All Hands - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Scavenger hunts are among the most high-energy team building events. These games are customizable to fit various venues and occasions.'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('17-09-2028');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core2 Contributor');
                cy.get('#root_start_date').clear().type('14-09-2028');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('20-09-2028');
                cy.get('body').click();
                cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Most scavenger hunts involve players getting into groups and racing against each other to find clue.');

                cy.get('#root_event_destination').clear('h');
                cy.get('#root_event_destination').type('houst');
                cy.get('#downshift-0-item-6 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('ma');
                cy.get('#root_departure_from').type('madrid');
                cy.get('#downshift-1-item-5 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('ma');
                cy.get('#root_return_to').type('madrid');
                cy.get('#downshift-2-item-5 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Examples might include “find a statue that reminds you of your boss,” '
                    );
                cy.get('#root_item_0_qty').clear().type('12');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('DAI');
                cy.get('#root_item_0_unit_price').type('986');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        '“show the oldest coin within your group’s wallets,” or “recreate the Crossing of the Delaware in.”'
                    );
                cy.get('#root_item_1_qty').clear().type('4');
                cy.get('#root_item_1_currency_type').select('Crypto');
                cy.get('#root_item_1_currency').select('ETH');
                cy.get('#root_item_1_unit_price').type('0.05');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        'typically, scavenger hunts have a theme and a time limit.'
                    );
                cy.get('#root_item_2_qty').clear().type('5');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('NZD');
                cy.get('#root_item_2_unit_price').type('976.75');

                cy.get('button')
                    .contains(/^Save and Close$/)
                    .click();

                cy.contains('Started by me', { timeout: 60000 });
                cy.logout();

            });
        });

        // Save and Close Few fields Form 1 - Meetup - Without Files
        it('Save and Close Few fields - Meetup - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Escape rooms are one of the most popular team building events for small groups. In these games, participants usually enter a locked themed room and have a limited time to find clues and solve a mystery to escape and win the game.'
                    );
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('12-11-2024');
                cy.get('body').click();
                //cy.get('#root_core_contributor').clear().type('Core3 Contributor');
                cy.get('#root_start_date').clear().type('10-11-2024');
                cy.get('body').click();
                //cy.get('#root_end_date').clear().type('14-11-2024');
                cy.get('body').click();
                cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                //cy.get('#root_event_name').clear().type('These challenges require team members to collaborate, communicate clearly, think critically.');

                cy.get('#root_event_destination').clear('me');
                cy.get('#root_event_destination').type('melbo');
                cy.get('#downshift-0-item-6 > .cds--list-box__menu-item__option').click();
                //cy.get('#root_departure_from').clear('c');
                //cy.get('#root_departure_from').type('copen');
                //cy.get('.cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('l');
                cy.get('#root_return_to').type('london');
                cy.get('#downshift-2-item-2 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Entertainment venues like malls often host these attractions, and there are usually at least one.'
                    );
                cy.get('#root_item_0_qty').clear().type('1');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('COP');
                //cy.get('#root_item_0_unit_price').type('3489');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1


                cy.get('button')
                    .contains(/^Save and Close$/)
                    .click();

                cy.contains('Started by me', { timeout: 60000 });
                cy.logout();
            });
        });

        // Save and Close Form 2 - Team Event - Without Files
        it('Save and Close Form 2 - Team Event - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Beach parties are a beloved summertime activity for work. These events allow employees to get out of the office and enjoy fresh air and sunshine.'
                    );
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('17-12-2023');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core4 Contributor');
                cy.get('#root_start_date').clear().type('06-12-2023');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('24-12-2023');
                cy.get('body').click();
                cy.get('#root_event_type').select('team_event');
                //cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('You can take your staff on a trip to the beach.');

                cy.get('#root_event_destination').clear('b');
                cy.get('#root_event_destination').type('bergen');
                cy.get('#downshift-0-item-9 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear();
                cy.get('#root_departure_from').type('bern');
                cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('B');
                cy.get('#root_return_to').type('Bern');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Create a beach-like atmosphere in your party space by handing out leis and serving tropical drinks.'
                    );
                cy.get('#root_item_0_qty').clear().type('3');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('ETH');
                cy.get('#root_item_0_unit_price').type('0.75');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Some ideas include putting up a volleyball net, handing out branded beach balls and sunglasses.'
                    );
                cy.get('#root_item_1_qty').clear().type('15');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('EUR');
                cy.get('#root_item_1_unit_price').type('235');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        'As a bonding exercise you can ask teammates to submit photos of their favorite beach or dream beach.'
                    );
                cy.get('#root_item_2_qty').clear().type('9');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('GBP');
                cy.get('#root_item_2_unit_price').type('765.35');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 3
                cy.get('#root_item_3_sub_category').select('tickets');
                cy.get('#root_item_3_item_name')
                    .clear()
                    .type(
                        'Beach parties are a beloved summertime activity for work'
                    );
                cy.get('#root_item_3_qty').clear().type('25');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('DAI');
                cy.get('#root_item_3_unit_price').type('245');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'You can take your staff on a trip to the beach or create a beach-like atmosphere in your party space by handing out leis and serving tropical drinks. Some ideas include putting up a volleyball net, handing out branded beach balls and sunglasses.'
                    );

                cy.get('button')
                    .contains(/^Save and Close$/)
                    .click();

                cy.contains('Started by me', { timeout: 60000 });
                cy.logout();
            });
        });

        // Cancel request Form 1 - Conference - Without Files
        it('Cancel request Form 1 - Conference - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Ultimate Trivia Showdown elevates pub trivia into a game-show-like atmosphere. For 90-minutes, a professional performer plays the role of host and leads teams in new takes on quiz games.'
                    );
                cy.get('#root_criticality').select('High');
                //cy.get('#root_period').clear().type('30-03-2026');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core5 Contributor');
                //cy.get('#root_start_date').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('01-04-2026');
                cy.get('body').click();
                cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Players collaborate against each other and compete against other teams to prove dominance.');

                //cy.get('#root_event_destination').clear('mi');
                //cy.get('#root_event_destination').type('miami');
                //cy.get('#downshift-0-item-1 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('mi');
                cy.get('#root_departure_from').type('milano');
                cy.get('#downshift-1-item-1 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('z');
                cy.get('#root_return_to').type('z');
                cy.get('#downshift-2-item-3 > .cds--list-box__menu-item__option').click();
                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Happen in a variety of indoor settings and can add a layer of fun and bonding to any team event.....'
                    );
                cy.get('#root_item_0_qty').clear().type('8');
                //cy.get('#root_item_0_currency_type').select('Crypto');
                //cy.get('#root_item_0_currency').select('SNT');
                //cy.get('#root_item_0_unit_price').type('2680');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                //Item 1 is not filled

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

        // Cancel request Form 2 - Conference - Without Files
        it('Cancel request Form 2 - Conference - Without Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Ultimate Trivia Showdown elevates pub trivia into a game-show-like atmosphere. For 90-minutes, a professional performer plays the role of host and leads teams in new takes on quiz games.'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core2 Contributor');
                cy.get('#root_start_date').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Players collaborate against each other and compete against other teams to prove dominance.');

                cy.get('#root_event_destination').clear('Zürich');
                cy.get('#root_event_destination').type('Zürich');
                cy.get('#downshift-0-item-6 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('t');
                cy.get('#root_departure_from').type('trondh');
                cy.get('.cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('S');
                cy.get('#root_return_to').type('New york');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();
                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Happen in a variety of indoor settings and can add a layer of fun and bonding to any team event.....'
                    );
                cy.get('#root_item_0_qty').clear().type('12');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('JPY');
                cy.get('#root_item_0_unit_price').type('2355.25');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Now you have all you need for your seamless flight. With a variety of services such as Flexi Ticket.'
                    );
                cy.get('#root_item_1_qty').clear().type('4');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('HKD');
                cy.get('#root_item_1_unit_price').type('4325');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A professional performer plays the role of host and leads teams in new takes on quiz games, like Majority Rules and Champion Challenge.'
                    );

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
        it('Arrange items order', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Ultimate Trivia Showdown elevates pub trivia into a game-show-like atmosphere. For 90-minutes, a professional performer plays the role of host and leads teams in new takes on quiz games.'
                    );
                cy.get('#root_criticality').select('Medium');
                cy.get('#root_period').clear().type('05-11-2027');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core1 Contributor');
                cy.get('#root_start_date').clear().type('30-10-2027');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('07-11-2027');
                cy.get('body').click();
                cy.get('#root_event_type').select('team_event');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Players collaborate against each other and compete against other teams to prove dominance.');

                cy.get('#root_event_destination').clear('st');
                cy.get('#root_event_destination').type('stockh');
                cy.get('#downshift-0-item-1 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('s');
                cy.get('#root_departure_from').type('san die');
                cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('s');
                cy.get('#root_return_to').type('san diego');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        '1.Happen in a variety of indoor settings and can add a layer of fun and bonding to any team event.'
                    );
                cy.get('#root_item_0_qty').clear().type('12');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('SNT');
                cy.get('#root_item_0_unit_price').type('1450.32');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        '2.Now you have all you need for your seamless flight. With a variety of services such as Ticket.'
                    );
                cy.get('#root_item_1_qty').clear().type('15');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('AED');
                cy.get('#root_item_1_unit_price').type('1980');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        '3. Typically, scavenger hunts have a theme and a time limit.'
                    );
                cy.get('#root_item_2_qty').clear().type('5');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('NZD');
                cy.get('#root_item_2_unit_price').type('976.75');

                cy.get('#root_item > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up').click();
                cy.get('#root_item > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-up').click();

                cy.wait(2000);

                cy.get('#root_item > div.row.array-item-list > div:nth-child(1) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-down').click();
                cy.get('#root_item > div.row.array-item-list > div:nth-child(2) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-default.array-item-move-down').click();

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A professional performer plays the role of host and leads teams in new takes on quiz games, like Majority Rules and Champion Challenge.'
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
                cy.wait(1000);

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

        // Delete items
        it('Delete items', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Scavenger hunts are among the most high-energy team building events. These games are customizable to fit various venues and occasions.'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('17-09-2028');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core2 Contributor');
                cy.get('#root_start_date').clear().type('14-09-2028');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('20-09-2028');
                cy.get('body').click();
                cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Most scavenger hunts involve players getting into groups and racing against each other to find clue.');

                cy.get('#root_event_destination').clear('h');
                cy.get('#root_event_destination').type('houst');
                cy.get('#downshift-0-item-6 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('ma');
                cy.get('#root_departure_from').type('madrid');
                cy.get('#downshift-1-item-5 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('ma');
                cy.get('#root_return_to').type('madrid');
                cy.get('#downshift-2-item-5 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        '1.Examples might include “find a statue that reminds you of your boss” '
                    );
                cy.get('#root_item_0_qty').clear().type('12');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('DAI');
                cy.get('#root_item_0_unit_price').type('986');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        '2.“show the oldest coin within your group’s wallets,” or “recreate the Crossing of the Delaware in.”'
                    );
                cy.get('#root_item_1_qty').clear().type('4');
                cy.get('#root_item_1_currency_type').select('Crypto');
                cy.get('#root_item_1_currency').select('ETH');
                cy.get('#root_item_1_unit_price').type('0.05');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        '3. Typically, scavenger hunts have a theme and a time limit.'
                    );
                cy.get('#root_item_2_qty').clear().type('5');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('NZD');
                cy.get('#root_item_2_unit_price').type('976.75');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 3
                cy.get('#root_item_3_sub_category').select('tickets');
                cy.get('#root_item_3_item_name')
                    .clear()
                    .type(
                        '4.Beach parties are a beloved summertime activity for work.'
                    );
                cy.get('#root_item_3_qty').clear().type('25');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('DAI');
                cy.get('#root_item_3_unit_price').type('245');

                //delete first and third items
                cy.get('#root_item > div.row.array-item-list > div:nth-child(3) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-danger.array-item-remove').click();
                cy.get('#root_item > div.row.array-item-list > div:nth-child(1) > div > div.cds--sm\\:col-span-1.cds--md\\:col-span-1.cds--lg\\:col-span-1.cds--css-grid-column > div > div > button.btn.btn-danger.array-item-remove').click();

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        '4.At the end of the game, the group that completes the most tasks or finds the most items wins the game and earns prize.'
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
                cy.wait(1000);

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

// Form validation
describe('Form validation', () => {

    //Special character check
    it('Special character check', () => {
        const username = Cypress.env('requestor_username');
        const password = Cypress.env('requestor_password');
        cy.log(`=====username : ${username}`);
        cy.log(`=====password : ${password}`);

        cy.login(username, password);
        cy.visit('/');

        cy.contains('Start New +').click();
        cy.contains('Coming soon - Request Travel').click();

        cy.runPrimaryBpmnFile(true);

        cy.contains('Coming soon - Request Travel', { timeout: 60000 });

        // cy.wait(5000);
        cy.url().then((currentUrl) => {
            // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
            // extract the digits after /tasks

            const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
            cy.log('==###############===processInstanceId : ', processInstanceId);
            const projectId = Cypress.env('project_id');
            cy.wait(2000);

            cy.get('#root_project').select(projectId);
            cy.get('#root_purpose')
                .clear()
                .type(
                    'Purpose is to test all the special characters work in the request. ~!@#$%^&*()_+`-= {}[]\a and ;\',./:"<>? end. | this text goes missing', { parseSpecialCharSequences: false }
                );
            cy.get('#root_criticality').select('High');
            cy.get('#root_period').clear().type('17-09-2028');
            cy.get('body').click();
            cy.get('#root_core_contributor').clear().type('Core2 Contributor');
            cy.get('#root_start_date').clear().type('14-09-2028');
            cy.get('body').click();
            cy.get('#root_end_date').clear().type('20-09-2028');
            cy.get('body').click();
            cy.get('#root_event_type').select('all_hands');
            cy.get('#root_event_name').clear().type('Special char test ,./;\'[]\b=-0987654321`~!@#$%^&*()_+{}:"<>? end.', { parseSpecialCharSequences: false });

            cy.get('#root_event_destination').clear('Tromsø');
            cy.get('#root_event_destination').type('Tromsø');
            cy.get('.cds--list-box__menu-item__option').click();
            cy.get('#root_departure_from').clear('Ålesund');
            cy.get('#root_departure_from').type('Ålesund');
            cy.get('.cds--list-box__menu-item__option').click();
            cy.get('#root_return_to').clear('Neuchâtel');
            cy.get('#root_return_to').type('Neuchâtel');
            cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();

            // item 0
            cy.get('#root_item_0_sub_category').select('accom');
            cy.get('#root_item_0_item_name')
                .clear()
                .type(
                    'Special char test ,./;\'[]\=-0987654321`~!@#$%^&*()_+{}:"<>? end.', { parseSpecialCharSequences: false }
                );
            cy.get('#root_item_0_qty').clear().type('12');
            cy.get('#root_item_0_currency_type').select('Crypto');
            cy.get('#root_item_0_currency').select('DAI');
            cy.get('#root_item_0_unit_price').type('986');

            cy.get('button')
                .contains(/^Submit$/)
                .click();

            cy.contains(
                'Task: Review the Request',
                { timeout: 60000 }
            );

            cy.get('.cds--text-area__wrapper')
                .find('#root')
                .type(
                    'Test Special chars afs<sfsd>sfsfs,asfdf. sfsf? sfd/sfs f:sfsf " sfsdf; SDFfsd\' sfsdf{sfsfs} sfsdf[ sfsdf] fsfsfd\ sfsd sfsdf=S dfs+ sfd- sfsdf_ sfsfd (sfsd )sfsfsd * sf&sfsfs ^ sfs % sf $ ss# s@ sf! sfd` ss~ END.', { parseSpecialCharSequences: false }
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
            cy.wait(1000);

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


    //Check field max lengths
    it('Check field max lengths', () => {
        const username = Cypress.env('requestor_username');
        const password = Cypress.env('requestor_password');
        cy.log(`=====username : ${username}`);
        cy.log(`=====password : ${password}`);

        cy.login(username, password);
        cy.visit('/');

        cy.contains('Start New +').click();
        cy.contains('Coming soon - Request Travel').click();

        cy.runPrimaryBpmnFile(true);

        cy.contains('Coming soon - Request Travel', { timeout: 60000 });

        // cy.wait(5000);
        cy.url().then((currentUrl) => {
            // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
            // extract the digits after /tasks

            const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
            cy.log('==###############===processInstanceId : ', processInstanceId);
            const projectId = Cypress.env('project_id');
            cy.wait(2000);

            cy.get('#root_project').select(projectId);
            cy.get('#root_purpose')
                .clear()
                .type(
                    'It’s easy to keep connected with others during online events. Online events are virtual, accessible, entertaining, and a great way to make new friends. Meetup has online events on topics like gaming, music, technology, networking, wellness, or whatever.'
                );
            cy.get('#root_criticality').select('Low');
            cy.get('#root_period').clear().type('27-02-2024');
            cy.get('body').click();
            cy.get('#root_core_contributor').clear().type('Core1 Contributor');
            cy.get('#root_start_date').clear().type('26-02-2024');
            cy.get('body').click();
            cy.get('#root_end_date').clear().type('04-03-2024');
            cy.get('body').click();
            cy.get('#root_event_type').select('meetup');
            //cy.get('#root_event_type').select('all_hands');
            cy.get('#root_event_name').clear().type('The most common times for happy hours -directly after work or during the final hours of the workday..');

            cy.get('#root_event_destination').clear('s');
            cy.get('#root_event_destination').type('sydney');
            cy.get('#downshift-0-item-2 > .cds--list-box__menu-item__option').click();
            cy.get('#root_departure_from').clear('o');
            cy.get('#root_departure_from').type('oslo');
            cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
            cy.get('#root_return_to').clear('ch');
            cy.get('#root_return_to').type('chica');
            cy.get('#downshift-2-item-1 > .cds--list-box__menu-item__option').click();

            // item 0
            cy.get('#root_item_0_sub_category').select('accom');
            cy.get('#root_item_0_item_name')
                .clear()
                .type(
                    'Entertainment ideas include answering icebreaker questions, playing pool or board games.1234567890123'
                );
            cy.get('#root_item_0_qty').clear().type('9');
            cy.get('#root_item_0_currency_type').select('Fiat');
            cy.get('#root_item_0_currency').select('CHF');
            cy.get('#root_item_0_unit_price').type('140.654');

            cy.get('#root_item > div:nth-child(3) > p > button').click();

            // item 1
            cy.get('#root_item_1_sub_category').select('flights');
            cy.get('#root_item_1_item_name')
                .clear()
                .type(
                    'You could assign a theme or leave the event more free-form encourage teammates to chat with peers...'
                );
            cy.get('#root_item_1_qty').clear().type('4');
            cy.get('#root_item_1_currency_type').select('Crypto');
            cy.get('#root_item_1_currency').select('DAI');
            cy.get('#root_item_1_unit_price').type('5689.1234');

            cy.get('button')
                .contains(/^Submit$/)
                .click();

            cy.contains(
                'Task: Review the Request',
                { timeout: 60000 }
            );

            cy.get('.cds--text-area__wrapper')
                .find('#root')
                .type(
                    'It’s easy to keep connected with others during online events. Online events are virtual, accessible, entertaining, and a great way to make new friends. Meetup has online events on topics like gaming, music, technology, networking, wellness, or whatever you’re looking for!'
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
            cy.wait(1000);

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

// Request Travel - With Files
describe('Request Travel - With Files', () => {
    Cypress._.times(1, () => {
        // Initiate request - Team Event - With Files
        it('Initiate request - Team Event - With Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Before you start planning your trip, make sure to check your company’s rules, procedures, and do’s & don’ts when it comes to corporate travel. Here you’ll find more information about corporate travel policies, which include things such as where to ..'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('17-09-2028');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core1 Contributor');
                cy.get('#root_start_date').clear().type('14-09-2028');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('20-09-2028');
                cy.get('body').click();
                cy.get('#root_event_type').select('team_event');
                //cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Great Guac Off is one of the best team building events. Participants compete in teams to perfect it.');

                cy.get('#root_event_destination').clear('y');
                cy.get('#root_event_destination').type('yellow');
                cy.get('#downshift-0-item-3 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('c');
                cy.get('#root_departure_from').type('colombo');
                cy.get('#downshift-1-item-1 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('s');
                cy.get('#root_return_to').type('spring');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Our staff can facilitate your accommodation needs from a range of Home-stay options and can also.'
                    );
                cy.get('#root_item_0_qty').clear().type('7');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('ETH');
                cy.get('#root_item_0_unit_price').type('1.15');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Now you have all you need for your seamless flight. With a variety of services such as Flexi Ticket.'
                    );
                cy.get('#root_item_1_qty').clear().type('5');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CAD');
                cy.get('#root_item_1_unit_price').type('2300');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        'Ensure a quality, cost effective and safe integrated transport system and services that will provi.'
                    );
                cy.get('#root_item_2_qty').clear().type('9');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('AUD');
                cy.get('#root_item_2_unit_price').type('1205.75');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 3
                cy.get('#root_item_3_sub_category').select('tickets');
                cy.get('#root_item_3_item_name')
                    .clear()
                    .type(
                        'Book Your Tickets In Advance And Get A Chance To Experience Unlimited Rides On 1 Day. Experience....'
                    );
                cy.get('#root_item_3_qty').clear().type('18');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('SNT');
                cy.get('#root_item_3_unit_price').type('430.50');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A host brings all the ingredients, leads groups through mini-games, and encourages participants to taunt or cheer. This cookless cook-off is available in various venues. https://teambuilding.com/blog/team-building-events'
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


                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.wait(6000);
                /*cy.get('button')
                    .contains(/^Return to Home$/)
                    .click();*/

                cy.contains('Process Instance Id:', { timeout: 60000 });
                cy.logout();
                cy.wait(1000);
            });
        });

        // Edit request - Meetup - With Files
        it('Edit request - Meetup - With Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Happy hours are a go-to team social event. These gatherings involve heading to a local watering hole, setting up a bar in the office, and socializing over drinks and snacks.'
                    );
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('27-02-2024');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core1 Contributor');
                cy.get('#root_start_date').clear().type('26-02-2024');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('04-03-2024');
                cy.get('body').click();
                cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('The most common times for happy hours -directly after work or during the final hours of the workday.');

                cy.get('#root_event_destination').clear('s');
                cy.get('#root_event_destination').type('sydney');
                cy.get('#downshift-0-item-2 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('o');
                cy.get('#root_departure_from').type('oslo');
                cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('ch');
                cy.get('#root_return_to').type('chica');
                cy.get('#downshift-2-item-1 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Entertainment ideas include answering icebreaker questions, playing pool or board games.'
                    );
                cy.get('#root_item_0_qty').clear().type('9');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('CHF');
                cy.get('#root_item_0_unit_price').type('140.65');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'You could assign a theme or leave the event more free-form encourage teammates to chat with peers.'
                    );
                cy.get('#root_item_1_qty').clear().type('4');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('CNY');
                cy.get('#root_item_1_unit_price').type('5689');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A professional performer plays the role of host and leads teams in new takes on quiz games, like Majority Rules and Champion Challenge.'
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


                cy.get('button')
                    .contains(/^Edit Request$/)
                    .click();

                // Form 1
                cy.contains('Task: Submit Details', { timeout: 60000 });
                cy.wait(2000);
                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                // Form 2
                cy.contains('Task: Review the Request', { timeout: 60000 });

                cy.get('.cds--text-area__wrapper').find('#root').type('EDITING INFO');
            });
        });

        // Save and Close Form 2 - Team Event - With Files
        it('Save and Close Form 2 - Team Event - With Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Beach parties are a beloved summertime activity for work. These events allow employees to get out of the office and enjoy fresh air and sunshine.'
                    );
                cy.get('#root_criticality').select('Low');
                cy.get('#root_period').clear().type('17-12-2023');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core4 Contributor');
                cy.get('#root_start_date').clear().type('06-12-2023');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('24-12-2023');
                cy.get('body').click();
                cy.get('#root_event_type').select('team_event');
                //cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('You can take your staff on a trip to the beach.');

                cy.get('#root_event_destination').clear('b');
                cy.get('#root_event_destination').type('bergen');
                cy.get('#downshift-0-item-9 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear();
                cy.get('#root_departure_from').type('bern');
                cy.get('#downshift-1-item-0 > .cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('B');
                cy.get('#root_return_to').type('Bern');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();

                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Create a beach-like atmosphere in your party space by handing out leis and serving tropical drinks.'
                    );
                cy.get('#root_item_0_qty').clear().type('3');
                cy.get('#root_item_0_currency_type').select('Crypto');
                cy.get('#root_item_0_currency').select('ETH');
                cy.get('#root_item_0_unit_price').type('0.75');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Some ideas include putting up a volleyball net, handing out branded beach balls and sunglasses.'
                    );
                cy.get('#root_item_1_qty').clear().type('15');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('EUR');
                cy.get('#root_item_1_unit_price').type('235');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 2
                cy.get('#root_item_2_sub_category').select('transport');
                cy.get('#root_item_2_item_name')
                    .clear()
                    .type(
                        'As a bonding exercise you can ask teammates to submit photos of their favorite beach or dream beach.'
                    );
                cy.get('#root_item_2_qty').clear().type('9');
                cy.get('#root_item_2_currency_type').select('Fiat');
                cy.get('#root_item_2_currency').select('GBP');
                cy.get('#root_item_2_unit_price').type('765.35');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 3
                cy.get('#root_item_3_sub_category').select('tickets');
                cy.get('#root_item_3_item_name')
                    .clear()
                    .type(
                        'Beach parties are a beloved summertime activity for work'
                    );
                cy.get('#root_item_3_qty').clear().type('25');
                cy.get('#root_item_3_currency_type').select('Crypto');
                cy.get('#root_item_3_currency').select('DAI');
                cy.get('#root_item_3_unit_price').type('245');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'You can take your staff on a trip to the beach or create a beach-like atmosphere in your party space by handing out leis and serving tropical drinks. Some ideas include putting up a volleyball net, handing out branded beach balls and sunglasses.'
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


                cy.get('button')
                    .contains(/^Save and Close$/)
                    .click();

                cy.contains('Started by me', { timeout: 60000 });
                cy.logout();
            });
        });

        // Cancel request Form 2 - Conference - With Files
        it('Cancel request Form 2 - Conference - With Files', () => {
            const username = Cypress.env('requestor_username');
            const password = Cypress.env('requestor_password');
            cy.log(`=====username : ${username}`);
            cy.log(`=====password : ${password}`);

            cy.login(username, password);
            cy.visit('/');

            cy.contains('Start New +').click();
            cy.contains('Coming soon - Request Travel').click();

            cy.runPrimaryBpmnFile(true);

            cy.contains('Coming soon - Request Travel', { timeout: 60000 });

            // cy.wait(5000);
            cy.url().then((currentUrl) => {
                // if url is "/tasks/8/d37c2f0f-016a-4066-b669-e0925b759560"
                // extract the digits after /tasks

                const processInstanceId = currentUrl.match(/(?<=\/tasks\/)\d+/)[0];
                cy.log('==###############===processInstanceId : ', processInstanceId);
                const projectId = Cypress.env('project_id');
                cy.wait(2000);

                cy.get('#root_project').select(projectId);
                cy.get('#root_purpose')
                    .clear()
                    .type(
                        'Ultimate Trivia Showdown elevates pub trivia into a game-show-like atmosphere. For 90-minutes, a professional performer plays the role of host and leads teams in new takes on quiz games.'
                    );
                cy.get('#root_criticality').select('High');
                cy.get('#root_period').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_core_contributor').clear().type('Core2 Contributor');
                cy.get('#root_start_date').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_end_date').clear().type('29-03-2026');
                cy.get('body').click();
                cy.get('#root_event_type').select('conf');
                //cy.get('#root_event_type').select('meetup');
                //cy.get('#root_event_type').select('all_hands');
                cy.get('#root_event_name').clear().type('Players collaborate against each other and compete against other teams to prove dominance.');

                cy.get('#root_event_destination').clear('Zürich');
                cy.get('#root_event_destination').type('Zürich');
                cy.get('#downshift-0-item-6 > .cds--list-box__menu-item__option').click();
                cy.get('#root_departure_from').clear('t');
                cy.get('#root_departure_from').type('trondh');
                cy.get('.cds--list-box__menu-item__option').click();
                cy.get('#root_return_to').clear('S');
                cy.get('#root_return_to').type('New york');
                cy.get('#downshift-2-item-0 > .cds--list-box__menu-item__option').click();
                // item 0
                cy.get('#root_item_0_sub_category').select('accom');
                cy.get('#root_item_0_item_name')
                    .clear()
                    .type(
                        'Happen in a variety of indoor settings and can add a layer of fun and bonding to any team event.....'
                    );
                cy.get('#root_item_0_qty').clear().type('12');
                cy.get('#root_item_0_currency_type').select('Fiat');
                cy.get('#root_item_0_currency').select('JPY');
                cy.get('#root_item_0_unit_price').type('2355.25');

                cy.get('#root_item > div:nth-child(3) > p > button').click();

                // item 1
                cy.get('#root_item_1_sub_category').select('flights');
                cy.get('#root_item_1_item_name')
                    .clear()
                    .type(
                        'Now you have all you need for your seamless flight. With a variety of services such as Flexi Ticket.'
                    );
                cy.get('#root_item_1_qty').clear().type('4');
                cy.get('#root_item_1_currency_type').select('Fiat');
                cy.get('#root_item_1_currency').select('HKD');
                cy.get('#root_item_1_unit_price').type('4325');

                cy.get('button')
                    .contains(/^Submit$/)
                    .click();

                cy.contains(
                    'Task: Review the Request',
                    { timeout: 60000 }
                );

                cy.get('.cds--text-area__wrapper')
                    .find('#root')
                    .type(
                        'A professional performer plays the role of host and leads teams in new takes on quiz games, like Majority Rules and Champion Challenge.'
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
    });
});