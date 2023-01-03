import { modifyProcessIdentifierForPathParam } from '../../src/helpers';
import { miscDisplayName } from '../support/helpers';

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
    const groupId = 'misc/acceptance-tests-group-one';
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Test Model 2 ${id}`;
    const modelId = `test-model-2-${id}`;
    const newModelDisplayName = `${modelDisplayName} edited`;
    cy.contains(miscDisplayName).click();
    cy.wait(500);
    cy.contains(groupDisplayName).click();
    cy.createModel(groupId, modelId, modelDisplayName);
    cy.url().should(
      'include',
      `process-models/${modifyProcessIdentifierForPathParam(
        groupId
      )}:${modelId}`
    );
    cy.contains(`Process Model: ${modelDisplayName}`);

    cy.getBySel('edit-process-model-button').click();
    cy.get('input[name=display_name]').clear().type(newModelDisplayName);
    cy.contains('Submit').click();
    cy.contains(`Process Model: ${newModelDisplayName}`);

    // go back to process model show by clicking on the breadcrumb
    cy.contains(modelDisplayName).click();

    cy.getBySel('delete-process-model-button').click();
    cy.contains('Are you sure');
    cy.getBySel('delete-process-model-button-modal-confirmation-dialog')
      .find('.cds--btn--danger')
      .click();
    cy.url().should(
      'include',
      `process-groups/${modifyProcessIdentifierForPathParam(groupId)}`
    );
    cy.contains(modelId).should('not.exist');
    cy.contains(modelDisplayName).should('not.exist');
  });

  it('can create new bpmn and dmn and json files', () => {
    const uuid = () => Cypress._.random(0, 1e6);
    const id = uuid();
    const directParentGroupId = 'acceptance-tests-group-one';
    const groupId = `misc/${directParentGroupId}`;
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Test Model 2 ${id}`;
    const modelId = `test-model-2-${id}`;

    const bpmnFileName = `bpmn_test_file_${id}`;
    const dmnFileName = `dmn_test_file_${id}`;
    const jsonFileName = `json_test_file_${id}`;

    cy.contains(miscDisplayName).click();
    cy.wait(500);
    cy.contains(groupDisplayName).click();
    cy.createModel(groupId, modelId, modelDisplayName);
    cy.contains(groupDisplayName).click();
    cy.contains(modelDisplayName).click();
    cy.url().should(
      'include',
      `process-models/${modifyProcessIdentifierForPathParam(
        groupId
      )}:${modelId}`
    );
    cy.contains(`Process Model: ${modelDisplayName}`);
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
    cy.contains(modelDisplayName).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
    // cy.getBySel('files-accordion').click();
    cy.contains(`${bpmnFileName}.bpmn`).should('exist');

    // add new dmn file
    cy.contains('New DMN File').click();
    cy.contains(/^Process Model File$/);
    cy.get('g[data-element-id=decision_1]').click().should('exist');
    cy.contains('General').click();
    cy.get('#bio-properties-panel-id')
      .clear()
      .type('decision_acceptance_test_1');
    cy.contains('General').click();
    cy.contains('Save').click();
    cy.get('input[name=file_name]').type(dmnFileName);
    cy.contains('Save Changes').click();
    cy.contains(`Process Model File: ${dmnFileName}`);
    cy.contains(modelDisplayName).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
    // cy.getBySel('files-accordion').click();
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
    cy.contains(modelDisplayName).click();
    cy.contains(`Process Model: ${modelDisplayName}`);
    // cy.getBySel('files-accordion').click();
    cy.contains(`${jsonFileName}.json`).should('exist');

    cy.getBySel('delete-process-model-button').click();
    cy.contains('Are you sure');
    cy.getBySel('delete-process-model-button-modal-confirmation-dialog')
      .find('.cds--btn--danger')
      .click();
    cy.url().should(
      'include',
      `process-groups/${modifyProcessIdentifierForPathParam(groupId)}`
    );
    cy.contains(modelId).should('not.exist');
    cy.contains(modelDisplayName).should('not.exist');

    // we go back to the parent process group after deleting the model
    cy.get('.tile-process-group-content-container').should('exist');
  });

  it('can upload and run a bpmn file', () => {
    const uuid = () => Cypress._.random(0, 1e6);
    const id = uuid();
    const directParentGroupId = 'acceptance-tests-group-one';
    const groupId = `misc/${directParentGroupId}`;
    const groupDisplayName = 'Acceptance Tests Group One';
    const modelDisplayName = `Test Model 2 ${id}`;
    const modelId = `test-model-2-${id}`;
    cy.contains('Add a process group');
    cy.contains(miscDisplayName).click();
    cy.wait(500);
    cy.contains(groupDisplayName).click();
    cy.createModel(groupId, modelId, modelDisplayName);

    cy.contains(`${groupDisplayName}`).click();
    cy.contains('Add a process model');
    cy.contains(modelDisplayName).click();
    cy.url().should(
      'include',
      `process-models/${modifyProcessIdentifierForPathParam(
        groupId
      )}:${modelId}`
    );
    cy.contains(`Process Model: ${modelDisplayName}`);

    cy.getBySel('upload-file-button').click();
    cy.contains('Add file').selectFile(
      'cypress/fixtures/test_bpmn_file_upload.bpmn'
    );
    cy.getBySel('modal-upload-file-dialog')
      .find('.cds--btn--primary')
      .contains('Upload')
      .click();
    cy.runPrimaryBpmnFile();

    // cy.getBySel('process-instance-list-link').click();
    cy.getBySel('process-instance-show-link').click();
    cy.getBySel('process-instance-delete').click();
    cy.contains('Are you sure');
    cy.getBySel('process-instance-delete-modal-confirmation-dialog')
      .find('.cds--btn--danger')
      .click();

    // in breadcrumb
    cy.contains(modelDisplayName).click();

    cy.getBySel('delete-process-model-button').click();
    cy.contains('Are you sure');
    cy.getBySel('delete-process-model-button-modal-confirmation-dialog')
      .find('.cds--btn--danger')
      .click();
    cy.url().should(
      'include',
      `process-groups/${modifyProcessIdentifierForPathParam(groupId)}`
    );
    cy.contains(modelId).should('not.exist');
    cy.contains(modelDisplayName).should('not.exist');
  });

  // process models no longer has pagination post-tiles
  // it.only('can paginate items', () => {
  //   cy.contains(miscDisplayName).click();
  //   cy.wait(500);
  //   cy.contains('Acceptance Tests Group One').click();
  //   cy.basicPaginationTest();
  // });

  it('can allow searching for model', () => {
    cy.getBySel('process-model-selection').click().type('model-3');
    cy.contains('acceptance-tests-group-one/acceptance-tests-model-3').click();
    cy.contains('Acceptance Tests Model 3');
  });
});
