import { format } from 'date-fns';
import { DATE_FORMAT, PROCESS_STATUSES } from '../../src/config';
import { titleizeString } from '../../src/helpers';

const filterByDate = (fromDate) => {
  cy.get('#date-picker-start-from').clear().type(format(fromDate, DATE_FORMAT));
  cy.contains('Start date to').click();
  cy.get('#date-picker-end-from').clear().type(format(fromDate, DATE_FORMAT));
  cy.contains('End date to').click();
  cy.getBySel('filter-button').click();
};

const updateDmnText = (oldText, newText, elementId = 'wonderful_process') => {
  // this will break if there are more elements added to the drd
  cy.get(`g[data-element-id=${elementId}]`).click().should('exist');
  cy.get('.dmn-icon-decision-table').click();
  cy.contains(oldText).clear().type(`"${newText}"`);

  // wait for a little bit for the xml to get set before saving
  // FIXME: gray out save button or add spinner while xml is loading
  cy.wait(500);
  cy.contains('Save').click();
};

const updateBpmnPythonScript = (pythonScript, elementId = 'process_script') => {
  cy.get(`g[data-element-id=${elementId}]`).click().should('exist');
  cy.contains(/^Script$/).click();
  cy.get('textarea[name="pythonScript_bpmn:script"]')
    .clear()
    .type(pythonScript);

  // wait for a little bit for the xml to get set before saving
  cy.wait(500);
  cy.contains('Save').click();
};

const updateBpmnPythonScriptWithMonaco = (
  pythonScript,
  elementId = 'process_script'
) => {
  cy.get(`g[data-element-id=${elementId}]`).click().should('exist');
  // sometimes, we click on the script task and panel doesn't update to include script task stuff. not sure why.
  cy.contains(/^Script$/).click();
  cy.contains('Launch Editor').click();
  // sometimes, Loading... appears for more than 4 seconds. not sure why.
  cy.contains('Loading...').should('not.exist');

  // the delay 30 is because, at some point, monaco started automatically
  // adding a second double quote when we type a double quote. when it does
  // that, there is a race condition where it sometimes gets in more text
  // before the second double quote appears because the robot is typing faster
  // than a human being could, so we artificially slow it down to make it more
  // human.
  cy.get('.monaco-editor textarea:first')
    .click()
    .focused() // change subject to currently focused element
    .clear()
    // long delay to ensure cypress isn't competing with monaco auto complete stuff
    .type(pythonScript, { delay: 120 });

  cy.contains('Close').click();
  // wait for a little bit for the xml to get set before saving
  cy.wait(500);
  cy.contains('Save').click();
};

describe('process-instances', () => {
  beforeEach(() => {
    cy.login();
    cy.navigateToProcessModel(
      'Acceptance Tests Group One',
      'Acceptance Tests Model 1'
    );
  });
  afterEach(() => {
    cy.logout();
  });

  it('can create a new instance and can modify', () => {
    const originalDmnOutputForKevin = 'Very wonderful';
    const newDmnOutputForKevin = 'The new wonderful';
    const dmnOutputForDan = 'pretty wonderful';
    const acceptanceTestOneDisplayName = 'Acceptance Tests Model 1';

    const originalPythonScript = 'person = "Kevin"';
    const newPythonScript = 'person = "Dan"';

    const dmnFile = 'awesome_decision.dmn';
    const bpmnFile = 'process_model_one.bpmn';

    cy.contains(originalDmnOutputForKevin).should('not.exist');
    cy.runPrimaryBpmnFile();

    // Change dmn
    cy.getBySel('files-accordion').click();
    cy.getBySel(`edit-file-${dmnFile.replace('.', '-')}`).click();
    updateDmnText(originalDmnOutputForKevin, newDmnOutputForKevin);

    cy.contains(acceptanceTestOneDisplayName).click();
    cy.runPrimaryBpmnFile();

    cy.getBySel('files-accordion').click();
    cy.getBySel(`edit-file-${dmnFile.replace('.', '-')}`).click();
    updateDmnText(newDmnOutputForKevin, originalDmnOutputForKevin);
    cy.contains(acceptanceTestOneDisplayName).click();
    cy.runPrimaryBpmnFile();

    // Change bpmn
    cy.getBySel('files-accordion').click();
    cy.getBySel(`edit-file-${bpmnFile.replace('.', '-')}`).click();
    cy.contains(`Process Model File: ${bpmnFile}`);
    updateBpmnPythonScript(newPythonScript);
    cy.contains(acceptanceTestOneDisplayName).click();
    cy.runPrimaryBpmnFile();

    cy.getBySel('files-accordion').click();
    cy.getBySel(`edit-file-${bpmnFile.replace('.', '-')}`).click();
    updateBpmnPythonScript(originalPythonScript);
    cy.contains(acceptanceTestOneDisplayName).click();
    cy.runPrimaryBpmnFile();
  });

  // it('can create a new instance and can modify with monaco text editor', () => {
  //   // leave off the ending double quote since manco adds it
  //   const originalPythonScript = 'person = "Kevin';
  //   const newPythonScript = 'person = "Mike';
  //
  //   const bpmnFile = 'process_model_one.bpmn';
  //
  //   // Change bpmn
  //   cy.getBySel('files-accordion').click();
  //   cy.getBySel(`edit-file-${bpmnFile.replace('.', '-')}`).click();
  //   cy.contains(`Process Model File: ${bpmnFile}`);
  //   updateBpmnPythonScriptWithMonaco(newPythonScript);
  //   cy.contains('acceptance-tests-model-1').click();
  //   cy.runPrimaryBpmnFile();
  //
  //   cy.getBySel('files-accordion').click();
  //   cy.getBySel(`edit-file-${bpmnFile.replace('.', '-')}`).click();
  //   cy.contains(`Process Model File: ${bpmnFile}`);
  //   updateBpmnPythonScriptWithMonaco(originalPythonScript);
  //   cy.contains('acceptance-tests-model-1').click();
  //   cy.runPrimaryBpmnFile();
  // });

  it('can paginate items', () => {
    // make sure we have some process instances
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();
    cy.runPrimaryBpmnFile();

    cy.getBySel('process-instance-list-link').click();
    cy.basicPaginationTest();
  });

  it('can display logs', () => {
    // make sure we have some process instances
    cy.runPrimaryBpmnFile();
    cy.getBySel('process-instance-list-link').click();
    cy.getBySel('process-instance-show-link-id').first().click();
    cy.getBySel('process-instance-log-list-link').click();
    cy.getBySel('process-instance-log-detailed').click();
    cy.contains('process_model_one');
    cy.contains('task_completed');
    cy.basicPaginationTest();
  });

  it('can filter', () => {
    cy.getBySel('process-instance-list-link').click();
    cy.getBySel('process-instance-list-all').click();
    cy.contains('All Process Instances');
    cy.assertAtLeastOneItemInPaginatedResults();

    cy.getBySel('filter-section-expand-toggle').click();

    const statusSelect = '#process-instance-status-select';
    PROCESS_STATUSES.forEach((processStatus) => {
      if (!['all', 'waiting'].includes(processStatus)) {
        cy.get(statusSelect).click();
        cy.get(statusSelect).contains(titleizeString(processStatus)).click();
        cy.get(statusSelect).click();
        cy.getBySel('filter-button').click();

        // make sure that there is 1 status item selected in the multiselect
        cy.get(`${statusSelect} .cds--tag`).contains('1');

        cy.assertAtLeastOneItemInPaginatedResults();
        cy.getBySel(`process-instance-status-${processStatus}`);

        // maybe waiting a bit before trying to click makes this work consistently?
        cy.wait(1000);
        // there should really only be one, but in CI there are sometimes more
        cy.get('div[aria-label="Clear all selected items"]:first').click();
        cy.get('div[aria-label="Clear all selected items"]').should(
          'not.exist'
        );
      }
    });

    const date = new Date();
    date.setHours(date.getHours() - 1);
    filterByDate(date);
    cy.assertAtLeastOneItemInPaginatedResults();

    date.setHours(date.getHours() + 26);
    filterByDate(date);
    cy.assertNoItemInPaginatedResults();
  });
});
