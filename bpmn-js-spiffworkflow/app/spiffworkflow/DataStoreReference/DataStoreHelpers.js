export function isDataStoreReferenced(process, dataStoreId) {
    const status = process.get('flowElements').some(elem =>
        elem.$type === 'bpmn:DataStoreReference' && elem.dataStoreRef && elem.dataStoreRef.id === dataStoreId
    );
    return status;
}

export function isDataStoreReferencedV2(definitions, dataStoreId) {
    return definitions.get('rootElements').some(elem =>
        elem.$type === 'bpmn:DataStoreReference' && elem.dataStoreRef && elem.dataStoreRef.id === dataStoreId
    );
}

export function removeDataStore(definitions, dataStoreId) {
    definitions.set('rootElements', definitions.get('rootElements').filter(elem =>
        !(elem.$type === 'bpmn:DataStore' && elem.id === dataStoreId)
    ));
}