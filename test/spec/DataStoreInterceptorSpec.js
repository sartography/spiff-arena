import { bootstrapPropertiesPanel, expectSelected } from './helpers';
import { BpmnPropertiesPanelModule, BpmnPropertiesProviderModule } from 'bpmn-js-properties-panel';
import {
    getBpmnJS,
    inject
} from 'bpmn-js/test/helper';
import dataStoreInterceptor from '../../app/spiffworkflow/DataStoreReference';

describe('DataStore Interceptor', function () {

    let xml = require('./bpmn/data_store.bpmn').default;

    beforeEach(bootstrapPropertiesPanel(xml, {
        debounceInput: false,
        additionalModules: [
            dataStoreInterceptor,
            BpmnPropertiesPanelModule,
            BpmnPropertiesProviderModule,
        ]
    }));


    it('should delete dataStore in case dataStoreRef is deleted - DataStoreReference element', inject(async function (modeling) {

        const modeler = getBpmnJS();
        
        // We Select a DataStoreReference element
        const shapeElement = await expectSelected('DataStoreReference_0eqeh4p');
        expect(shapeElement, "I can't find DataStoreReference element").to.exist;

        let definitions = await modeler.getDefinitions();
        let dataStoreExists = definitions.get('rootElements').some(element =>
            element.$type === 'bpmn:DataStore' && element.id === 'countries'
        );
        expect(dataStoreExists, "DataStore 'countries' should be added at the root level").to.be.true;

        // Remove dataStoreReference
        await modeler.get('modeling').removeShape(shapeElement);
        const nwshapeElement = await expectSelected('DataStoreReference_0eqeh4p');
        expect(nwshapeElement, "I can't find DataStoreReference element").not.to.exist;

        // Check that DataStore foods is removed from the root of the process
        definitions = await modeler.getDefinitions();
        dataStoreExists = definitions.get('rootElements').some(element =>
            element.$type === 'bpmn:DataStore' && element.id === 'countries'
        );
        expect(dataStoreExists, "DataStore 'countries' should be removed from the root level").not.to.be.true;
    }));

});
