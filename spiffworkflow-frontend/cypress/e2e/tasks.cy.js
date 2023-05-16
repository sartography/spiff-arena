const submitInputIntoFormField = (taskName, fieldKey, fieldValue) => {
  cy.contains(`Task: ${taskName}`, { timeout: 10000 });
  cy.get(fieldKey).clear();
  cy.get(fieldKey).type(fieldValue);
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
    'Acceptance Tests Model 2'
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

    submitInputIntoFormField('get_form_num_one', '#root_form_num_1', 2);
    submitInputIntoFormField('get_form_num_two', '#root_form_num_2', 3);

    cy.contains('Task: get_form_num_three');
    // TODO: remove this if we decide to completely kill form navigation
    // cy.getBySel('form-nav-form2').click();
    // checkFormFieldIsReadOnly(
    //   'get_form_num_two',
    //   '#root_form_num_2'
    // );
    // cy.getBySel('form-nav-form1').click();
    // checkFormFieldIsReadOnly(
    //   'get_form_num_one',
    //   '#root_form_num_1'
    // );
    //
    // cy.getBySel('form-nav-form3').click();
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
    cy.contains('Status: complete');
  });

  it('can paginate items', () => {
    // make sure we have some tasks
    kickOffModelWithForm();
    kickOffModelWithForm();
    kickOffModelWithForm();
    kickOffModelWithForm();
    kickOffModelWithForm();

    cy.navigateToHome();
    cy.basicPaginationTest('process-instance-show-link-id');
  });
});
