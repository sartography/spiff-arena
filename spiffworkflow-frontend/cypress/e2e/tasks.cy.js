const submitInputIntoFormField = (
  taskName,
  fieldKey,
  fieldValue,
  checkDraftData,
) => {
  cy.contains(`Task: ${taskName}`, { timeout: 10000 });
  cy.get(fieldKey).clear();
  cy.get(fieldKey).type(fieldValue);
  // wait a little bit after typing for the debounce to take effect
  cy.wait(100);

  // after a bit of a debounce period, the site automatically saves the data the user has been entering in user task forms.
  // if that doesn't work, it's not great.
  // so to test that, we reload the page and make sure the data they entered is not lost.
  if (checkDraftData) {
    cy.wait(1000);
    cy.reload();
    cy.get(fieldKey).should('have.value', fieldValue);
  }

  cy.contains('Submit').click();
};

// const checkFormFieldIsReadOnly = (formName, fieldKey) => {
//   cy.contains(`Task: ${formName}`);
//   cy.get(fieldKey).invoke('attr', 'disabled').should('exist');
// };

const checkTaskHasClass = (taskName, className) => {
  cy.get(`g[data-element-id=${taskName}]`).should('have.class', className);
};

const kickOffModelWithForm = () => {
  cy.navigateToProcessModel(
    'Acceptance Tests Group One',
    'Acceptance Tests Model 2',
  );
  cy.runPrimaryBpmnFile(true);
};

describe('tasks', () => {
  beforeEach(() => {
    cy.login();
  });
  afterEach(() => {
    cy.logout();
  });

  it('can complete and navigate a form', () => {
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Acceptance Tests Model 2`;
    const completedTaskClassName = 'completed-task-highlight';
    const activeTaskClassName = 'active-task-highlight';

    cy.navigateToProcessModel(groupDisplayName, modelDisplayName);
    cy.runPrimaryBpmnFile(true);

    submitInputIntoFormField('get_form_num_one', '#root_form_num_1', 2, true);
    submitInputIntoFormField('get_form_num_two', '#root_form_num_2', 3);

    cy.contains('Task: get_form_num_three');
    submitInputIntoFormField('get_form_num_three', '#root_form_num_3', 4);

    cy.contains('Task: get_form_num_four');
    cy.navigateToProcessModel(groupDisplayName, modelDisplayName);
    cy.getBySel('process-instance-list-link').click();
    cy.assertAtLeastOneItemInPaginatedResults();

    // This should get the first one which should be the one we just completed
    cy.getBySel('process-instance-show-link-id').first().click();
    cy.contains('Process Instance Id: ');

    cy.get(`g[data-element-id=form3]`).click();
    cy.contains('"form_num_1": 2');
    cy.contains('"form_num_2": 3');
    cy.contains('"form_num_3": 4');
    cy.contains('"form_num_4": 5').should('not.exist');
    checkTaskHasClass('form1', completedTaskClassName);
    checkTaskHasClass('form2', completedTaskClassName);
    checkTaskHasClass('form3', completedTaskClassName);
    checkTaskHasClass('form4', activeTaskClassName);
    cy.get('.is-visible .cds--modal-close').click();

    cy.navigateToHome();

    // look for somethig to make sure the homepage has loaded
    cy.contains('Waiting for me').should('exist');

    // FIXME: this will probably need a better way to link to the proper form that we want
    cy.contains('Go').click();

    submitInputIntoFormField('get_form_num_four', '#root_form_num_4', 5);
    cy.url().should('include', '/tasks');

    cy.navigateToProcessModel(groupDisplayName, modelDisplayName);
    cy.getBySel('process-instance-list-link').click();
    cy.assertAtLeastOneItemInPaginatedResults();

    // This should get the first one which should be the one we just completed
    cy.getBySel('process-instance-show-link-id').first().click();
    cy.contains('Process Instance Id: ');
    cy.get('.process-instance-status').contains('complete');
  });
});

describe('public_tasks', () => {
  it('can start process from message form', () => {
    // login and log out to ensure permissions are set correctly
    cy.login();
    cy.logout();

    cy.visit('public/misc:bounty_start_multiple_forms');
    cy.get('#root_firstName').type('MyFirstName');
    cy.contains('Submit').click();
    cy.get('#root_lastName').type('MyLastName');
    cy.contains('Submit').click();
    cy.contains('We hear you. Your name is MyFirstName MyLastName.');
  });

  it('can complete a guest task', () => {
    cy.login();
    const groupDisplayName = 'Shared Resources';
    const modelDisplayName = 'task-with-guest-form';
    cy.navigateToProcessModel(groupDisplayName, modelDisplayName);
    cy.runPrimaryBpmnFile(false, false, false);

    cy.get('[data-qa="metadata-value-first_task_url"] a')
      .invoke('attr', 'href')
      .then((hrefValue) => {
        cy.logout();
        cy.visit(hrefValue);
        // form 1
        cy.contains('Submit').click();
        // form 2
        cy.contains('Submit').click();
        cy.contains('You are done. Yay!');
        cy.visit(hrefValue);
        cy.contains('Error retrieving content.');
        cy.getBySel('public-home-link').click();
        cy.getBySel('public-sign-out').click();
        if (Cypress.env('SPIFFWORKFLOW_FRONTEND_AUTH_WITH_KEYCLOAK') === true) {
          cy.contains('Sign in to your account');
        } else {
          cy.get('#spiff-login-button').should('exist');
        }
      });
  });
});
