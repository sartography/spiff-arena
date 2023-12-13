import TestContainer from 'mocha-test-container-support';
import {
    BpmnPropertiesPanelModule,
    BpmnPropertiesProviderModule,
} from 'bpmn-js-properties-panel';
import { getBusinessObject } from 'bpmn-js/lib/util/ModelUtil';
import {
    bootstrapPropertiesPanel,
    changeInput,
    expectSelected,
    findGroupEntry,
    findEntry,
    findSelect,
    getPropertiesPanel
} from './helpers';

import { getBpmnJS, inject } from 'bpmn-js/test/helper';

import spiffModdleExtension from '../../app/spiffworkflow/moddle/spiffworkflow.json';
import DataStoreReference from '../../app/spiffworkflow/DataStoreReference';
import DataStoreInterceptor from '../../app/spiffworkflow/DataStoreReference/DataStoreInterceptor';

const return_datastores = (event) => {
    event.eventBus.fire('spiff.data_stores.returned', {
        options: [
            { type: 'typeahead', name: 'countries' },
            { type: 'kkv', name: 'foods' }
        ],
    });
}

describe('Data Source Reference Test cases', function () {
    const xml = require('./bpmn/data_store.bpmn').default;
    let container;

    beforeEach(function () {
        container = TestContainer.get(this);
    });

    beforeEach(
        bootstrapPropertiesPanel(xml, {
            container,
            debounceInput: false,
            additionalModules: [
                DataStoreReference,
                DataStoreInterceptor,
                BpmnPropertiesPanelModule,
                BpmnPropertiesProviderModule,
            ],
            moddleExtensions: {
                spiffworkflow: spiffModdleExtension,
            },
        })
    );

    it('should display the custom data store properties group - DataStoreReference element', async function () {
        // We Select a DataStoreReference element
        const shapeElement = await expectSelected('DataStoreReference_0eqeh4p');
        expect(shapeElement, "I can't find DataStoreReference element").to.exist;

        // Lets Check if the custom properties group is displayed
        const customGroup = findGroupEntry('custom-datastore-properties', container);
        expect(customGroup).to.exist;
        const entry = findEntry('selectDataStore', container);
        expect(entry).to.exist;
    });

    it('should list data sources from aa api response and append it to select - DataStoreReference element', async function () {
        const modeler = getBpmnJS();
        modeler.get('eventBus').once('spiff.data_stores.requested', return_datastores);

        // We Select a DataStoreReference element
        const shapeElement = await expectSelected('DataStoreReference_0eqeh4p');
        expect(shapeElement, "I can't find DataStoreReference element").to.exist;

        // Interact with the DataStoreSelect component
        const selectGroup = findGroupEntry('custom-datastore-properties', container)
        expect(selectGroup).to.exist;

        const entry = findEntry('selectDataStore', getPropertiesPanel());
        expect(entry).to.exist;

        // Verification if the dataStoreRef attribute is updated
        let selector = findSelect(entry);
        expect(selector.length).to.equal(3);
        expect(selector[1].value === 'countries');
        expect(selector[2].value === 'foods');
    });

    it('should update dataStoreRef after a select event && should add new DataState in the level of process definition - DataStoreReference element', async function () {
        const modeler = getBpmnJS();
        modeler.get('eventBus').once('spiff.data_stores.requested', return_datastores);

        // We Select a DataStoreReference element
        const shapeElement = await expectSelected('DataStoreReference_0eqeh4p');
        expect(shapeElement, "I can't find DataStoreReference element").to.exist;

        // Interact with the DataStoreSelect component
        const selectGroup = findGroupEntry('custom-datastore-properties', container)
        expect(selectGroup).to.exist;

        const entry = findEntry('selectDataStore', getPropertiesPanel());
        expect(entry).to.exist;

        // Verification if the dataStoreRef attribute is updated
        let selector = findSelect(entry);
        changeInput(selector, 'foods');
        const nwbusinessObject = getBusinessObject(shapeElement);
        expect(nwbusinessObject.get('dataStoreRef').id).to.equal('foods');

        // Check if the DataStore is added at the root level
        const definitions = modeler.getDefinitions();
        const dataStoreExists = definitions.get('rootElements').some(element =>
            element.$type === 'bpmn:DataStore' && element.id === 'foods'
        );
        expect(dataStoreExists, "DataStore 'foods' should be added at the root level").to.be.true;

    });

    it('should delete dataStore if dataStorRef is updated - DataStoreReference element', async function () {
        const modeler = getBpmnJS();
        modeler.get('eventBus').once('spiff.data_stores.requested', return_datastores);

        // We Select a DataStoreReference element
        const shapeElement = await expectSelected('DataStoreReference_0eqeh4p');
        expect(shapeElement, "I can't find DataStoreReference element").to.exist;

        // Interact with the DataStoreSelect component
        const selectGroup = findGroupEntry('custom-datastore-properties', container)
        expect(selectGroup).to.exist;

        const entry = findEntry('selectDataStore', getPropertiesPanel());
        expect(entry).to.exist;

        // Verification if the dataStoreRef attribute is updated
        let selector = findSelect(entry);
        changeInput(selector, 'foods');
        let nwbusinessObject = getBusinessObject(shapeElement);
        expect(nwbusinessObject.get('dataStoreRef').id).to.equal('foods');
        // Then choose new dataStore
        changeInput(selector, 'countries');
        nwbusinessObject = getBusinessObject(shapeElement);
        expect(nwbusinessObject.get('dataStoreRef').id).to.equal('countries');

        // Check if the DataStore is added at the root level with the updated dataStore
        const definitions = modeler.getDefinitions();
        const countriesDataStoreExists = definitions.get('rootElements').some(element =>
            element.$type === 'bpmn:DataStore' && element.id === 'countries'
        );
        expect(countriesDataStoreExists, "DataStore 'countries' should be added at the root level").to.be.true;
        const foodsDataStoreExists = definitions.get('rootElements').some(element =>
            element.$type === 'bpmn:DataStore' && element.id === 'foods'
        );
        expect(foodsDataStoreExists, "DataStore 'countries' should be removed from the root level").not.to.be.true;

    });

});
