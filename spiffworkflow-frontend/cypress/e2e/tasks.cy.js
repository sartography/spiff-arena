const submitInputIntoFormField = (taskName, fieldKey, fieldValue) => {
  cy.contains(`Task: ${taskName}`, { timeout: 10000 });
  cy.get(fieldKey).clear().type(fieldValue);
  cy.contains('Submit').click();
};

const checkFormFieldIsReadOnly = (formName, fieldKey) => {
  cy.contains(`Task: ${formName}`);
  cy.get(fieldKey).invoke('attr', 'disabled').should('exist');
};

const checkTaskHasClass = (taskName, className) => {
  cy.get(`g[data-element-id=${taskName}]`).should('have.class', className);
};

const kickOffModelWithForm = (modelId, formName) => {
  cy.navigateToProcessModel(
    'Acceptance Tests Group One',
    'Acceptance Tests Model 2',
    'acceptance-tests-model-2'
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
    const modelId = `acceptance-tests-model-2`;
    const modelDisplayName = `Acceptance Tests Model 2`;
    const completedTaskClassName = 'completed-task-highlight';
    const activeTaskClassName = 'active-task-highlight';

    cy.navigateToProcessModel(groupDisplayName, modelDisplayName, modelId);
    cy.runPrimaryBpmnFile(true);

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

    cy.getBySel('form-nav-form3').click();
    submitInputIntoFormField(
      'get_user_generated_number_three',
      '#root_user_generated_number_3',
      4
    );

    cy.contains('Task: get_user_generated_number_four');
    cy.navigateToProcessModel(groupDisplayName, modelDisplayName, modelId);
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
    cy.get('.is-visible .cds--modal-close').click();

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

    cy.navigateToProcessModel(groupDisplayName, modelDisplayName, modelId);
    cy.getBySel('process-instance-list-link').click();
    cy.assertAtLeastOneItemInPaginatedResults();

    // This should get the first one which should be the one we just completed
    cy.getBySel('process-instance-show-link').first().click();
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
    cy.basicPaginationTest();
  });
});
