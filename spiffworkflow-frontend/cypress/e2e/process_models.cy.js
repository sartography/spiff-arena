describe('process-models', () => {
  beforeEach(() => {
    cy.login();
  });
  afterEach(() => {
    cy.logout();
  });

  it('can perform crud operations', () => {
    const uuid = () => Cypress._.random(0, 1e6);
    const id = uuid();
    const groupId = 'acceptance-tests-group-one';
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Test Model 2 ${id}`;
    const newModelDisplayName = `${modelDisplayName} edited`;
    const modelId = `test-model-2-${id}`;
    cy.contains(groupDisplayName).click();
    cy.createModel(groupId, modelId, modelDisplayName);
    cy.url().should('include', `process-models/${groupId}:${modelId}`);
    cy.contains(`Process Model: ${modelDisplayName}`);

    cy.contains('Edit process model').click();
    cy.get('input[name=display_name]').clear().type(newModelDisplayName);
    cy.contains('Submit').click();
    cy.contains(`Process Model: ${groupId}/${modelId}`);
    cy.contains('Submit').click();
    cy.get('input[name=display_name]').should(
      'have.value',
      newModelDisplayName
    );

    cy.contains('Delete').click();
    cy.contains('Are you sure');
    cy.getBySel('modal-confirmation-dialog').find('.cds--btn--danger').click();
    cy.url().should('include', `process-groups/${groupId}`);
    cy.contains(modelId).should('not.exist');
  });

  it('can create new bpmn, dmn, and json files', () => {
    const uuid = () => Cypress._.random(0, 1e6);
    const id = uuid();
    const groupId = 'acceptance-tests-group-one';
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Test Model 2 ${id}`;
    const modelId = `test-model-2-${id}`;

    const bpmnFileName = `bpmn_test_file_${id}`;
    const dmnFileName = `dmn_test_file_${id}`;
    const jsonFileName = `json_test_file_${id}`;

    cy.contains(groupDisplayName).click();
    cy.createModel(groupId, modelId, modelDisplayName);
    cy.contains(groupId).click();
    cy.contains(modelId).click();
    cy.url().should('include', `process-models/${groupId}:${modelId}`);
    cy.contains(`Process Model: ${modelDisplayName}`);
    cy.getBySel('files-accordion').click();
    cy.contains(`${bpmnFileName}.bpmn`).should('not.exist');
    cy.contains(`${dmnFileName}.dmn`).should('not.exist');
    cy.contains(`${jsonFileName}.json`).should('not.exist');

    // add new bpmn file
    cy.contains('New BPMN File').click();
    cy.contains(/^Process Model File$/);
    cy.get('g[data-element-id=StartEvent_1]').click().should('exist');
    cy.contains('General').click();
    cy.get('#bio-properties-panel-name').clear().type('Start Event Name');
    cy.wait(500);
    cy.contains('Save').click();
    cy.contains('Start Event Name');
    cy.get('input[name=file_name]').type(bpmnFileName);
    cy.contains('Save Changes').click();
    cy.contains(`Process Model File: ${bpmnFileName}`);
    cy.contains(modelId).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
    cy.getBySel('files-accordion').click();
    cy.contains(`${bpmnFileName}.bpmn`).should('exist');

    // add new dmn file
    cy.contains('New DMN File').click();
    cy.contains(/^Process Model File$/);
    cy.get('g[data-element-id=decision_1]').click().should('exist');
    cy.contains('General').click();
    cy.contains('Save').click();
    cy.get('input[name=file_name]').type(dmnFileName);
    cy.contains('Save Changes').click();
    cy.contains(`Process Model File: ${dmnFileName}`);
    cy.contains(modelId).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
    cy.getBySel('files-accordion').click();
    cy.contains(`${dmnFileName}.dmn`).should('exist');

    // add new json file
    cy.contains('New JSON File').click();
    cy.contains(/^Process Model File$/);
    // Some reason, cypress evals json strings so we have to escape it it with '{{}'
    cy.get('.view-line').type('{{} "test_key": "test_value" }');
    cy.getBySel('file-save-button').click();
    cy.get('input[name=file_name]').type(jsonFileName);
    cy.contains('Save Changes').click();
    cy.contains(`Process Model File: ${jsonFileName}`);
    // wait for json to load before clicking away to avoid network errors
    cy.wait(500);
    cy.contains(modelId).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
    cy.getBySel('files-accordion').click();
    cy.contains(`${jsonFileName}.json`).should('exist');

    cy.contains('Edit process model').click();
    cy.contains('Delete').click();
    cy.contains('Are you sure');
    cy.getBySel('modal-confirmation-dialog').find('.cds--btn--danger').click();
    cy.url().should('include', `process-groups/${groupId}`);
    cy.contains(modelId).should('not.exist');
  });

  it('can upload and run a bpmn file', () => {
    const uuid = () => Cypress._.random(0, 1e6);
    const id = uuid();
    const groupId = 'acceptance-tests-group-one';
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Test Model 2 ${id}`;
    const modelId = `test-model-2-${id}`;
    cy.contains('Add a process group');
    cy.contains(groupDisplayName).click();
    cy.createModel(groupId, modelId, modelDisplayName);

    cy.contains(`${groupId}`).click();
    cy.contains('Add a process model');
    cy.contains(modelId).click();
    cy.url().should('include', `process-models/${groupId}:${modelId}`);
    cy.contains(`Process Model: ${modelDisplayName}`);

    cy.getBySel('files-accordion').click();
    cy.getBySel('upload-file-button').click();
    cy.contains('Add file').selectFile(
      'cypress/fixtures/test_bpmn_file_upload.bpmn'
    );
    cy.getBySel('modal-upload-file-dialog')
      .find('.cds--btn--primary')
      .contains('Upload')
      .click();
    cy.runPrimaryBpmnFile();

    cy.getBySel('process-instance-list-link').click();
    cy.getBySel('process-instance-show-link').click();
    cy.getBySel('process-instance-delete').click();
    cy.contains('Are you sure');
    cy.getBySel('modal-confirmation-dialog').find('.cds--btn--danger').click();

    // in breadcrumb
    cy.contains(modelId).click();

    cy.contains('Edit process model').click();
    cy.contains('Delete').click();
    cy.contains('Are you sure');
    cy.getBySel('modal-confirmation-dialog').find('.cds--btn--danger').click();
    cy.url().should('include', `process-groups/${groupId}`);
    cy.contains(modelId).should('not.exist');
  });

  it('can paginate items', () => {
    cy.contains('Acceptance Tests Group One').click();
    cy.basicPaginationTest();
  });

  it('can allow searching for model', () => {
    cy.getBySel('process-model-selection').click().type('model-3');
    cy.contains('acceptance-tests-group-one/acceptance-tests-model-3').click();
    cy.contains('List').click();
  });
});
