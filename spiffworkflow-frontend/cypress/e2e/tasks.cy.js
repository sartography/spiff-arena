const submitInputIntoFormField = (taskName, fieldKey, fieldValue) => {
  cy.contains(`Task: ${taskName}`);
  cy.get(fieldKey).clear().type(fieldValue);
  cy.contains('Submit').click();
};

const checkFormFieldIsReadOnly = (formName, fieldKey) => {
  cy.contains(`Task: ${formName}`);
  cy.get(fieldKey).invoke('attr', 'readonly').should('exist');
};

const checkTaskHasClass = (taskName, className) => {
  cy.get(`g[data-element-id=${taskName}]`).should('have.class', className);
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
    const modelId = `acceptance-tests-model-2`;
    const completedTaskClassName = 'completed-task-highlight';
    const activeTaskClassName = 'active-task-highlight';

    cy.navigateToProcessModel(groupDisplayName, modelId);

    // avoid reloading so we can click on the task link that appears on running the process instance
    cy.runPrimaryBpmnFile(false);

    cy.contains('my task').click();

    submitInputIntoFormField(
      'get_user_generated_number_one',
      '#root_user_generated_number_1',
      2
    );
    submitInputIntoFormField(
      'get_user_generated_number_two',
      '#root_user_generated_number_2',
      3
    );

    cy.contains('Task: get_user_generated_number_three');
    cy.getBySel('form-nav-form2').click();
    checkFormFieldIsReadOnly(
      'get_user_generated_number_two',
      '#root_user_generated_number_2'
    );
    cy.getBySel('form-nav-form1').click();
    checkFormFieldIsReadOnly(
      'get_user_generated_number_one',
      '#root_user_generated_number_1'
    );

    cy.getBySel('form-nav-form3').should('have.text', 'form3 - Current');
    cy.getBySel('form-nav-form3').click();
    submitInputIntoFormField(
      'get_user_generated_number_three',
      '#root_user_generated_number_3',
      4
    );

    cy.contains('Task: get_user_generated_number_four');
    cy.navigateToProcessModel(groupDisplayName, modelId);
    cy.getBySel('process-instance-list-link').click();
    cy.assertAtLeastOneItemInPaginatedResults();

    // This should get the first one which should be the one we just completed
    cy.getBySel('process-instance-show-link').first().click();
    cy.contains('Process Instance Id: ');

    cy.get(`g[data-element-id=form3]`).click();
    cy.contains('"user_generated_number_1": 2');
    cy.contains('"user_generated_number_2": 3');
    cy.contains('"user_generated_number_3": 4');
    cy.contains('"user_generated_number_4": 5').should('not.exist');
    checkTaskHasClass('form1', completedTaskClassName);
    checkTaskHasClass('form2', completedTaskClassName);
    checkTaskHasClass('form3', completedTaskClassName);
    checkTaskHasClass('form4', activeTaskClassName);
    cy.get('.modal .btn-close').click();

    cy.navigateToHome();
    cy.contains('Tasks').should('exist');

    // FIXME: this will probably need a better way to link to the proper form that we want
    cy.contains('Complete Task').click();

    submitInputIntoFormField(
      'get_user_generated_number_four',
      '#root_user_generated_number_4',
      5
    );
    cy.url().should('include', '/tasks');

    cy.navigateToProcessModel(groupDisplayName, modelId);
    cy.getBySel('process-instance-list-link').click();
    cy.assertAtLeastOneItemInPaginatedResults();

    // This should get the first one which should be the one we just completed
    cy.getBySel('process-instance-show-link').first().click();
    cy.contains('Process Instance Id: ');
    cy.contains('Status: complete');
  });

  it('can paginate items', () => {
    cy.navigateToProcessModel(
      'Acceptance Tests Group One',
      'acceptance-tests-model-2'
    );

    // make sure we have some tasks
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();

    cy.navigateToHome();
    cy.basicPaginationTest();
  });
});
